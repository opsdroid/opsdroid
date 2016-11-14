"""Core components of OpsDroid."""

import logging
import sys
import weakref
import asyncio

from opsdroid.helper import match
from opsdroid.memory import Memory
from opsdroid.connector import Connector
from opsdroid.database import Database
from opsdroid.loader import Loader


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
        logging.info("Created main opsdroid object")

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

    def exit(self):
        """Exit application."""
        logging.info("Exiting application with return code " +
                     str(self.sys_status))
        if self.eventloop.is_running():
            self.eventloop.stop()
        sys.exit(self.sys_status)

    def critical(self, error, code):
        """Exit due to unrecoverable error."""
        self.sys_status = code
        logging.critical(error)
        print("Error: " + error)
        self.exit()

    def load(self):
        """Load configuration."""
        self.config = self.loader.load_config_file([
            "./configuration.yaml",
            "~/.opsdroid/configuration.yaml",
            "/etc/opsdroid/configuration.yaml"
            ])

    def start_loop(self):
        """Start the event loop."""
        connectors, databases, skills = self.loader.load_config(self.config)
        if databases is not None:
            self.start_databases(databases)
        self.setup_skills(skills)
        self.start_connector_tasks(connectors)
        try:
            self.eventloop.run_forever()
        except (KeyboardInterrupt, EOFError):
            print('')  # Prints a character return for return to shell
            logging.info("Keyboard interrupt, exiting.")
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
                    connector_module["config"]["bot-name"] = self.bot_name
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
            logging.warning("All databases failed to load")
        for database_module in databases:
            for name, cls in database_module["module"].__dict__.items():
                if isinstance(cls, type) and \
                   issubclass(cls, Database) and \
                   cls is not Database:
                    logging.debug("Adding database: " + name)
                    database = cls(database_module["config"])
                    self.memory.databases.append(database)
                    database.connect(self)

    def load_regex_skill(self, regex, skill):
        """Load skills."""
        self.skills.append({"regex": regex, "skill": skill})

    async def parse(self, message):
        """Parse a string against all skills."""
        if message.text.strip() != "":
            logging.debug("Parsing input: " + message.text)
            for skill in self.skills:
                if "regex" in skill:
                    regex = match(skill["regex"], message.text)
                    if regex:
                        message.regex = regex
                        return await skill["skill"](self, message)
