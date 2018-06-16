"""Core components of OpsDroid."""

import copy
import logging
import os
import signal
import sys
import weakref
import asyncio
import contextlib

from opsdroid.memory import Memory
from opsdroid.connector import Connector
from opsdroid.database import Database
from opsdroid.loader import Loader
from opsdroid.parsers.always import parse_always
from opsdroid.parsers.regex import parse_regex
from opsdroid.parsers.dialogflow import parse_dialogflow
from opsdroid.parsers.luisai import parse_luisai
from opsdroid.parsers.recastai import parse_recastai
from opsdroid.parsers.witai import parse_witai
from opsdroid.parsers.rasanlu import parse_rasanlu, train_rasanlu
from opsdroid.parsers.crontab import parse_crontab
from opsdroid.const import DEFAULT_CONFIG_PATH


_LOGGER = logging.getLogger(__name__)


class OpsDroid():
    """Root object for opsdroid."""

    # pylint: disable=too-many-instance-attributes
    # All are reasonable in this case.

    instances = []

    def __init__(self):
        """Start opsdroid."""
        self.bot_name = 'opsdroid'
        self.sys_status = 0
        self.connectors = []
        self.connector_tasks = []
        self.eventloop = asyncio.get_event_loop()
        if os.name != 'nt':
            for sig in (signal.SIGINT, signal.SIGTERM):
                self.eventloop.add_signal_handler(sig, self.call_stop)
        self.skills = []
        self.memory = Memory()
        self.loader = Loader(self)
        self.config = {}
        self.stats = {
            "messages_parsed": 0,
            "webhooks_called": 0,
            "total_response_time": 0,
            "total_responses": 0,
        }
        self.web_server = None
        self.stored_path = []

    def __enter__(self):
        """Add self to existing instances."""
        self.stored_path = copy.copy(sys.path)
        if not self.__class__.instances:
            self.__class__.instances.append(weakref.proxy(self))
        else:
            self.critical("opsdroid has already been started", 1)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Remove self from existing instances."""
        sys.path = self.stored_path
        self.__class__.instances = []
        asyncio.set_event_loop(asyncio.new_event_loop())

    @property
    def default_connector(self):
        """Return the default connector."""
        default_connector = None
        for connector in self.connectors:
            if "default" in connector.config and connector.config["default"]:
                default_connector = connector
                break
        if default_connector is None:
            default_connector = self.connectors[0]
        return default_connector

    def exit(self):
        """Exit application."""
        _LOGGER.info(_("Exiting application with return code %s"),
                     str(self.sys_status))
        sys.exit(self.sys_status)

    def critical(self, error, code):
        """Exit due to unrecoverable error."""
        self.sys_status = code
        _LOGGER.critical(error)
        self.exit()

    def call_stop(self):
        """Signal handler to call disconnect and stop."""
        future = asyncio.ensure_future(self.disconnect())
        future.add_done_callback(self.stop)
        return future

    async def disconnect(self):
        """Disconnect all the connectors."""
        for connector in self.connectors:
            await connector.disconnect(self)

    def stop(self, future=None):
        """Stop the event loop."""
        pending = asyncio.Task.all_tasks()
        for task in pending:
            task.cancel()
        self.eventloop.stop()
        print('')  # Prints a character return for return to shell
        _LOGGER.info(_("Keyboard interrupt, exiting."))

    def load(self):
        """Load configuration."""
        self.config = self.loader.load_config_file([
            "configuration.yaml",
            DEFAULT_CONFIG_PATH,
            "/etc/opsdroid/configuration.yaml"
            ])

    def start_loop(self):
        """Start the event loop."""
        connectors, databases, skills = \
            self.loader.load_modules_from_config(self.config)
        _LOGGER.debug(_("Loaded %i skills"), len(skills))
        if databases is not None:
            self.start_databases(databases)
        self.setup_skills(skills)
        self.train_parsers(skills)
        self.start_connector_tasks(connectors)
        self.eventloop.create_task(parse_crontab(self))
        self.web_server.start()
        try:
            pending = asyncio.Task.all_tasks()
            self.eventloop.run_until_complete(asyncio.gather(*pending))
        except RuntimeError as error:
            if str(error) != 'Event loop is closed':
                raise error
        finally:
            self.eventloop.close()

    def setup_skills(self, skills):
        """Call the setup function on the passed in skills."""
        with contextlib.suppress(AttributeError):
            for skill in skills:
                skill["module"].setup(self)

    def train_parsers(self, skills):
        """Train the parsers."""
        if "parsers" in self.config:
            parsers = self.config["parsers"] or []
            tasks = []
            rasanlu = [p for p in parsers if p["name"] == "rasanlu"]
            if len(rasanlu) == 1 and \
                    ("enabled" not in rasanlu[0] or
                     rasanlu[0]["enabled"] is not False):
                tasks.append(
                    asyncio.ensure_future(
                        train_rasanlu(rasanlu[0], skills),
                        loop=self.eventloop))
            self.eventloop.run_until_complete(
                asyncio.gather(*tasks, loop=self.eventloop))

    def start_connector_tasks(self, connectors):
        """Start the connectors."""
        for connector_module in connectors:
            for _, cls in connector_module["module"].__dict__.items():
                if isinstance(cls, type) and \
                   issubclass(cls, Connector) and\
                   cls is not Connector:
                    connector = cls(connector_module["config"])
                    self.connectors.append(connector)

        if connectors:
            for connector in self.connectors:
                self.eventloop.run_until_complete(connector.connect(self))
            for connector in self.connectors:
                task = self.eventloop.create_task(connector.listen(self))
                self.connector_tasks.append(task)
        else:
            self.critical("All connectors failed to load", 1)

    def start_databases(self, databases):
        """Start the databases."""
        if not databases:
            _LOGGER.debug(databases)
            _LOGGER.warning(_("All databases failed to load"))
        for database_module in databases:
            for name, cls in database_module["module"].__dict__.items():
                if isinstance(cls, type) and \
                   issubclass(cls, Database) and \
                   cls is not Database:
                    _LOGGER.debug(_("Adding database: %s"), name)
                    database = cls(database_module["config"])
                    self.memory.databases.append(database)
                    self.eventloop.run_until_complete(database.connect(self))

    async def run_skill(self, skill, config, message):
        """Execute a skill."""
        # pylint: disable=broad-except
        # We want to catch all exceptions coming from a skill module and not
        # halt the application. If a skill throws an exception it just doesn't
        # give a response to the user, so an error response should be given.
        try:
            await skill(self, config, message)
        except Exception:
            if message:
                await message.respond(_("Whoops there has been an error"))
                await message.respond(_("Check the log for details"))
            _LOGGER.exception(_("Exception when running skill '%s' "),
                              str(config["name"]))

    async def get_ranked_skills(self, message):
        """Take a message and return a ranked list of matching skills."""
        skills = []
        skills = skills + await parse_regex(self, message)

        if "parsers" in self.config:
            _LOGGER.debug(_("Processing parsers..."))
            parsers = self.config["parsers"] or []

            dialogflow = [p for p in parsers if p["name"] == "dialogflow"
                          or p["name"] == "apiai"]

            # Show deprecation message but  parse message
            # Once it stops working remove this bit
            apiai = [p for p in parsers if p["name"] == "apiai"]
            if apiai:
                _LOGGER.warning(_("Api.ai is now called Dialogflow. This "
                                  "parser will stop working in the future "
                                  "please swap: 'name: apiai' for "
                                  "'name: dialogflow' in configuration.yaml"))

            if len(dialogflow) == 1 and \
                    ("enabled" not in dialogflow[0] or
                     dialogflow[0]["enabled"] is not False):
                _LOGGER.debug(_("Checking dialogflow..."))
                skills = skills + \
                    await parse_dialogflow(self, message, dialogflow[0])

            luisai = [p for p in parsers if p["name"] == "luisai"]
            if len(luisai) == 1 and \
                    ("enabled" not in luisai[0] or
                     luisai[0]["enabled"] is not False):
                _LOGGER.debug("Checking luisai...")
                skills = skills + \
                    await parse_luisai(self, message, luisai[0])

            recastai = [p for p in parsers if p["name"] == "recastai"]
            if len(recastai) == 1 and \
                    ("enabled" not in recastai[0] or
                     recastai[0]["enabled"] is not False):
                _LOGGER.debug(_("Checking Recast.AI..."))
                skills = skills + \
                    await parse_recastai(self, message, recastai[0])

            witai = [p for p in parsers if p["name"] == "witai"]
            if len(witai) == 1 and \
                    ("enabled" not in witai[0] or
                     witai[0]["enabled"] is not False):
                _LOGGER.debug(_("Checking wit.ai..."))
                skills = skills + \
                    await parse_witai(self, message, witai[0])

            rasanlu = [p for p in parsers if p["name"] == "rasanlu"]
            if len(rasanlu) == 1 and \
                    ("enabled" not in rasanlu[0] or
                     rasanlu[0]["enabled"] is not False):
                _LOGGER.debug(_("Checking Rasa NLU..."))
                skills = skills + \
                    await parse_rasanlu(self, message, rasanlu[0])

        return sorted(skills, key=lambda k: k["score"], reverse=True)

    async def parse(self, message):
        """Parse a string against all skills."""
        self.stats["messages_parsed"] = self.stats["messages_parsed"] + 1
        tasks = []
        if message.text.strip() != "":
            _LOGGER.debug(_("Parsing input: %s"), message.text)

            tasks.append(
                self.eventloop.create_task(parse_always(self, message)))

            ranked_skills = await self.get_ranked_skills(message)
            if ranked_skills:
                tasks.append(
                    self.eventloop.create_task(
                        self.run_skill(ranked_skills[0]["skill"],
                                       ranked_skills[0]["config"],
                                       message)))

        return tasks
