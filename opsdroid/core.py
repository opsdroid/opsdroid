"""Core components of OpsDroid."""

import copy
import logging
import os
import signal
import sys
import weakref
import asyncio
import contextlib
import inspect

from opsdroid import events
from opsdroid.const import DEFAULT_CONFIG_PATH
from opsdroid.memory import Memory
from opsdroid.connector import Connector
from opsdroid.database import Database
from opsdroid.skill import Skill
from opsdroid.loader import Loader
from opsdroid.web import Web
from opsdroid.parsers.always import parse_always
from opsdroid.parsers.event_type import parse_event_type
from opsdroid.parsers.regex import parse_regex
from opsdroid.parsers.parseformat import parse_format
from opsdroid.parsers.dialogflow import parse_dialogflow
from opsdroid.parsers.luisai import parse_luisai
from opsdroid.parsers.sapcai import parse_sapcai
from opsdroid.parsers.witai import parse_witai
from opsdroid.parsers.rasanlu import parse_rasanlu, train_rasanlu
from opsdroid.parsers.crontab import parse_crontab


_LOGGER = logging.getLogger(__name__)


class OpsDroid():
    """Root object for opsdroid."""

    # pylint: disable=too-many-instance-attributes
    # All are reasonable in this case.

    instances = []

    def __init__(self, config=None):
        """Start opsdroid."""
        self.bot_name = 'opsdroid'
        self._running = False
        self.sys_status = 0
        self.connectors = []
        self.connector_tasks = []
        self.eventloop = asyncio.get_event_loop()
        if os.name != 'nt':
            for sig in (signal.SIGINT, signal.SIGTERM):
                self.eventloop.add_signal_handler(
                    sig,
                    lambda: asyncio.ensure_future(self.handle_signal()))
        self.eventloop.set_exception_handler(self.handle_async_exception)
        self.skills = []
        self.memory = Memory()
        self.modules = {}
        self.cron_task = None
        self.loader = Loader(self)
        if config is None:
            self.config = {}
        else:
            self.config = config
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

    @staticmethod
    def handle_async_exception(loop, context):
        """Handle exceptions from async coroutines."""
        if "future" in context:
            try:  # pragma: nocover
                context['future'].result()
            # pylint: disable=broad-except
            except Exception:  # pragma: nocover
                _LOGGER.exception(_("Caught exception"))
        else:
            _LOGGER.error(_("Caught exception"))
        _LOGGER.error(context)

    def is_running(self):
        """Check whether opsdroid is running."""
        return self._running

    async def handle_signal(self):
        """Handle signals."""
        self._running = False
        await self.unload()

    def run(self):
        """Start the event loop."""
        _LOGGER.info(_("Opsdroid is now running, press ctrl+c to exit."))
        if not self.is_running():
            self._running = True
            while self.is_running():
                pending = asyncio.Task.all_tasks()
                with contextlib.suppress(asyncio.CancelledError):
                    self.eventloop.run_until_complete(asyncio.gather(*pending))

            self.eventloop.stop()
            self.eventloop.close()

            _LOGGER.info(_("Bye!"))
            self.exit()
        else:
            _LOGGER.error(_("Oops! Opsdroid is already running."))

    def load(self):
        """Load modules."""
        self.modules = self.loader.load_modules_from_config(self.config)
        _LOGGER.debug(_("Loaded %i skills"), len(self.modules["skills"]))
        self.setup_skills(self.modules["skills"])
        self.web_server = Web(self)
        self.web_server.setup_webhooks(self.skills)
        self.train_parsers(self.modules["skills"])
        if self.modules["databases"] is not None:
            self.start_databases(self.modules["databases"])
        self.start_connectors(self.modules["connectors"])
        self.cron_task = self.eventloop.create_task(parse_crontab(self))
        self.eventloop.create_task(self.web_server.start())

    async def unload(self, future=None):
        """Stop the event loop."""
        _LOGGER.info(_("Received stop signal, exiting."))

        _LOGGER.info(_("Removing skills..."))
        for skill in self.skills:
            _LOGGER.info(_("Removed %s"), skill.config['name'])
            self.skills.remove(skill)

        for connector in self.connectors:
            _LOGGER.info(_("Stopping connector %s..."), connector.name)
            await connector.disconnect()
            self.connectors.remove(connector)
            _LOGGER.info(_("Stopped connector %s"), connector.name)

        for database in self.memory.databases:
            _LOGGER.info(_("Stopping database %s..."), database.name)
            await database.disconnect()
            self.memory.databases.remove(database)
            _LOGGER.info(_("Stopped database %s"), database.name)

        _LOGGER.info(_("Stopping web server..."))
        await self.web_server.stop()
        self.web_server = None
        _LOGGER.info(_("Stopped web server"))

        _LOGGER.info(_("Stopping cron..."))
        self.cron_task.cancel()
        self.cron_task = None
        _LOGGER.info(_("Stopped cron"))

        _LOGGER.info(_("Stopping pending tasks..."))
        tasks = asyncio.Task.all_tasks()
        for task in list(tasks):
            if not task.done() and task is not asyncio.Task.current_task():
                task.cancel()
        _LOGGER.info(_("Stopped pending tasks"))

    async def reload(self):
        """Reload opsdroid."""
        await self.unload()
        self.config = Loader.load_config_file([
            "configuration.yaml",
            DEFAULT_CONFIG_PATH,
            "/etc/opsdroid/configuration.yaml"
        ])
        self.load()

    def setup_skills(self, skills):
        """Call the setup function on the loaded skills.

        Iterates through all the skills which have been loaded and runs
        any setup functions which have been defined in the skill.

        Args:
            skills (list): A list of all the loaded skills.

        """
        for skill in skills:
            for func in skill["module"].__dict__.values():
                if (isinstance(func, type) and
                        issubclass(func, Skill) and
                        func != Skill):
                    skill_obj = func(self, skill['config'])

                    for name in skill_obj.__dir__():
                        # pylint: disable=broad-except
                        # Getting an attribute of
                        # an object might raise any type of exceptions, for
                        # example within an external library called from an
                        # object property.  Since we are only interested in
                        # skill methods, we can safely ignore these.
                        try:
                            method = getattr(skill_obj, name)
                        except Exception:
                            continue

                        if hasattr(method, 'skill'):
                            self.skills.append(method)

                    continue

                if hasattr(func, "skill"):
                    _LOGGER.warning(_("Function based skills are deprecated "
                                      "and will be removed in a future "
                                      "release. Please use class-based skills "
                                      "instead."))
                    func.config = skill['config']
                    self.skills.append(func)

        with contextlib.suppress(AttributeError):
            for skill in skills:
                skill["module"].setup(self, self.config)
                _LOGGER.warning(_("<skill module>.setup() is deprecated and "
                                  "will be removed in a future release. "
                                  "Please use class-based skills instead."))

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

    def start_connectors(self, connectors):
        """Start the connectors."""
        for connector_module in connectors:
            for _, cls in connector_module["module"].__dict__.items():
                if isinstance(cls, type) and \
                   issubclass(cls, Connector) and\
                   cls is not Connector:
                    connector = cls(connector_module["config"], self)
                    self.connectors.append(connector)

        if connectors:
            for connector in self.connectors:
                if self.eventloop.is_running():
                    self.eventloop.create_task(connector.connect())
                else:
                    self.eventloop.run_until_complete(connector.connect())
            for connector in self.connectors:
                task = self.eventloop.create_task(connector.listen())
                self.connector_tasks.append(task)
        else:
            self.critical("All connectors failed to load", 1)

    # pylint: disable=W0640
    @property
    def _connector_names(self):  # noqa: D401
        """Mapping of names to connector instances."""
        if not self.connectors:
            raise ValueError("No connectors have been started")

        names = {}
        for connector in self.connectors:
            name = connector.config.get("name", connector.name)
            # Deduplicate any names
            if name in names:
                # Calculate the number of keys in names which start with name.
                n_key = len(list(filter(lambda x: x.startswith(name), names)))
                name += "_{}".format(n_key)
            names[name] = connector

        return names

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
                    self.eventloop.run_until_complete(database.connect())

    async def run_skill(self, skill, config, message):
        """Execute a skill."""
        # pylint: disable=broad-except
        # We want to catch all exceptions coming from a skill module and not
        # halt the application. If a skill throws an exception it just doesn't
        # give a response to the user, so an error response should be given.
        try:
            if len(inspect.signature(skill).parameters.keys()) > 1:
                await skill(self, config, message)
            else:
                await skill(message)
        except Exception:
            if message:
                await message.respond(events.Message(
                    _("Whoops there has been an error")))
                await message.respond(events.Message(
                    _("Check the log for details")))

            _LOGGER.exception(_("Exception when running skill '%s' "),
                              str(config["name"]))

    async def get_ranked_skills(self, skills, message):
        """Take a message and return a ranked list of matching skills."""
        ranked_skills = []
        if isinstance(message, events.Message):
            ranked_skills += await parse_regex(self, skills, message)
            ranked_skills += await parse_format(self, skills, message)
        ranked_skills += await parse_event_type(self, message)

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
                ranked_skills += \
                    await parse_dialogflow(self, skills,
                                           message, dialogflow[0])

            luisai = [p for p in parsers if p["name"] == "luisai"]
            if len(luisai) == 1 and \
                    ("enabled" not in luisai[0] or
                     luisai[0]["enabled"] is not False):
                _LOGGER.debug("Checking luisai...")
                ranked_skills += \
                    await parse_luisai(self, skills,
                                       message, luisai[0])

            sapcai = [p for p in parsers if p["name"] == "sapcai"]
            if len(sapcai) == 1 and \
                    ("enabled" not in sapcai[0] or
                     sapcai[0]["enabled"] is not False):
                _LOGGER.debug(_("Checking Recast.AI..."))
                ranked_skills += \
                    await parse_sapcai(self, skills,
                                       message, sapcai[0])

            witai = [p for p in parsers if p["name"] == "witai"]
            if len(witai) == 1 and \
                    ("enabled" not in witai[0] or
                     witai[0]["enabled"] is not False):
                _LOGGER.debug(_("Checking wit.ai..."))
                ranked_skills += \
                    await parse_witai(self, skills,
                                      message, witai[0])

            rasanlu = [p for p in parsers if p["name"] == "rasanlu"]
            if len(rasanlu) == 1 and \
                    ("enabled" not in rasanlu[0] or
                     rasanlu[0]["enabled"] is not False):
                _LOGGER.debug(_("Checking Rasa NLU..."))
                ranked_skills += \
                    await parse_rasanlu(self, skills,
                                        message, rasanlu[0])

        return sorted(ranked_skills, key=lambda k: k["score"], reverse=True)

    async def _constrain_skills(self, skills, message):
        """Remove skills with contraints which prohibit them from running.

        Args:
            skills (list): A list of skills to be checked for constraints.
            message (opsdroid.events.Message): The message currently being
                parsed.

        Returns:
            list: A list of the skills which were not constrained.

        """
        return [
            skill for skill in skills if all(
                constraint(message)
                for constraint in skill.constraints
            )
        ]

    async def parse(self, event):
        """Parse a string against all skills."""
        self.stats["messages_parsed"] = self.stats["messages_parsed"] + 1
        tasks = []
        if isinstance(event, events.Event):
            _LOGGER.debug(_("Parsing input: %s"), event)

            tasks.append(
                self.eventloop.create_task(parse_always(self, event)))

            unconstrained_skills = await self._constrain_skills(
                self.skills, event)
            ranked_skills = await self.get_ranked_skills(
                unconstrained_skills, event)
            if ranked_skills:
                tasks.append(
                    self.eventloop.create_task(
                        self.run_skill(ranked_skills[0]["skill"],
                                       ranked_skills[0]["config"],
                                       ranked_skills[0]["message"])))

        return tasks

    async def send(self, event):
        """Send an event.

        If ``event.connector`` is not set this method will use
        `OpsDroid.default_connector`. If ``event.connector`` is a string, it
        will be resolved to the name of the connectors configured in this
        instance.

        Args:
            event (opsdroid.events.Event): The event to send.

        """
        if isinstance(event.connector, str):
            event.connector = self._connector_names[event.connector]

        if not event.connector:
            event.connector = self.default_connector

        return await event.connector.send(event)
