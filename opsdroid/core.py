"""Core components of OpsDroid."""

import logging
import sys
import weakref
from multiprocessing import Process
from opsdroid.helper import match
from opsdroid.memory import Memory


class OpsDroid():
    """Root object for opsdroid."""

    instances = []

    def __init__(self):
        """Start opsdroid."""
        self.bot_name = 'opsdroid'
        self.sys_status = 0
        self.connectors = []
        self.connector_jobs = []
        self.skills = []
        self.memory = Memory()
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
        sys.exit(self.sys_status)

    def critical(self, error, code):
        """Exit due to unrecoverable error."""
        self.sys_status = code
        logging.critical(error)
        print("Error: " + error)
        self.exit()

    def start_connectors(self, connectors):
        """Start the connectors."""
        if len(connectors) == 0:
            self.critical("All connectors failed to load", 1)
        for connector_module in connectors:
            for name, cls in connector_module["module"].__dict__.items():
                if isinstance(cls, type) and "Connector" in name:
                    connector_module["config"]["bot-name"] = self.bot_name
                    connector = cls(connector_module["config"])
                    self.connectors.append(connector)
                    job = Process(target=connector.connect, args=(self,))
                    job.start()
                    self.connector_jobs.append(job)
        for job in self.connector_jobs:
            job.join()

    def start_databases(self, databases):
        """Start the databases."""
        if len(databases) == 0:
            logging.warning("All databases failed to load")
        for database_module in databases:
            for name, cls in database_module["module"].__dict__.items():
                if isinstance(cls, type) and "Database" in name:
                    logging.debug("Adding database: " + name)
                    database = cls(database_module["config"])
                    self.memory.databases.append(database)
                    database.connect()

    def load_regex_skill(self, regex, skill):
        """Load skills."""
        self.skills.append({"regex": regex, "skill": skill})

    def parse(self, message):
        """Parse a string against all skills."""
        if message.text.strip() != "":
            logging.debug("Parsing input: " + message.text)
            for skill in self.skills:
                if "regex" in skill:
                    regex = match(skill["regex"], message.text)
                    if regex:
                        message.regex = regex
                        skill["skill"](self, message)
