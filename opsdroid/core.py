"""Core components of OpsDroid."""

import logging
import sys
import weakref
import asyncio
import os.path

from opsdroid.memory import Memory
from opsdroid.connector import Connector
from opsdroid.database import Database
from opsdroid.loader import Loader
from opsdroid.parsers.regex import parse_regex
from opsdroid.parsers.apiai import parse_apiai
from opsdroid.parsers.crontab import parse_crontab


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
        _LOGGER.info("Created main opsdroid object")

    def __enter__(self):
        """Add self to existing instances."""
        if len(self.__class__.instances) == 0:
            self.__class__.instances.append(weakref.proxy(self))
        else:
            self.critical("opsdroid has already been started", 1)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Remove self from existing instances."""
        self.__class__.instances = []

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
        _LOGGER.info("Exiting application with return code " +
                     str(self.sys_status))
        if self.eventloop.is_running():
            self.eventloop.close()
        sys.exit(self.sys_status)

    def critical(self, error, code):
        """Exit due to unrecoverable error."""
        self.sys_status = code
        _LOGGER.critical(error)
        print("Error: " + error)
        self.exit()

    def load(self):
        """Load configuration."""
        self.config = self.loader.load_config_file([
            "./configuration.yaml",
            os.path.join(os.path.expanduser("~"),
                         ".opsdroid/configuration.yaml"),
            "/etc/opsdroid/configuration.yaml"
            ])

    def start_loop(self):
        """Start the event loop."""
        connectors, databases, skills = self.loader.load_config(self.config)
        if databases is not None:
            self.start_databases(databases)
        self.setup_skills(skills)
        self.start_connector_tasks(connectors)
        self.eventloop.create_task(parse_crontab(self))
        self.web_server.start()
        try:
            self.eventloop.run_forever()
        except (KeyboardInterrupt, EOFError):
            print('')  # Prints a character return for return to shell
            _LOGGER.info("Keyboard interrupt, exiting.")
        finally:
            self.exit()

    def setup_skills(self, skills):
        """Call the setup function on the passed in skills."""
        for skill in skills:
            try:
                skill["module"].setup(self)
            except AttributeError:
                pass

    def start_connector_tasks(self, connectors):
        """Start the connectors."""
        for connector_module in connectors:
            for _, cls in connector_module["module"].__dict__.items():
                if isinstance(cls, type) and \
                   issubclass(cls, Connector) and\
                   cls is not Connector:
                    connector = cls(connector_module["config"])
                    self.connectors.append(connector)

        if len(connectors) > 0:
            for connector in self.connectors:
                self.eventloop.run_until_complete(connector.connect(self))
            for connector in self.connectors:
                task = self.eventloop.create_task(connector.listen(self))
                self.connector_tasks.append(task)
        else:
            self.critical("All connectors failed to load", 1)

    def start_databases(self, databases):
        """Start the databases."""
        if len(databases) == 0:
            _LOGGER.debug(databases)
            _LOGGER.warning("All databases failed to load")
        for database_module in databases:
            for name, cls in database_module["module"].__dict__.items():
                if isinstance(cls, type) and \
                   issubclass(cls, Database) and \
                   cls is not Database:
                    _LOGGER.debug("Adding database: " + name)
                    database = cls(database_module["config"])
                    self.memory.databases.append(database)
                    self.eventloop.run_until_complete(database.connect(self))

    async def parse(self, message):
        """Parse a string against all skills."""
        self.stats["messages_parsed"] = self.stats["messages_parsed"] + 1
        tasks = []
        if message.text.strip() != "":
            _LOGGER.debug("Parsing input: " + message.text)

            tasks.append(
                self.eventloop.create_task(parse_regex(self, message)))

            if "parsers" in self.config:
                _LOGGER.debug("Processing parsers")
                parsers = self.config["parsers"]

                apiai = [p for p in parsers if p["name"] == "apiai"]
                _LOGGER.debug("Checking apiai")
                if len(apiai) == 1 and \
                        ("enabled" not in apiai[0] or
                         apiai[0]["enabled"] is not False):
                    _LOGGER.debug("Parsing with apiai")
                    tasks.append(
                        self.eventloop.create_task(
                            parse_apiai(self, message, apiai[0])))
        return tasks
