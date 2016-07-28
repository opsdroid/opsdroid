""" Core components of OpsDroid """

import logging
import sys
import re
import weakref

class OpsDroid():
    """ Root object for opsdroid """
    instances = []

    def __init__(self):
        """ opsdroid initialiser """
        # TODO Check instances and only allow one to be created
        self.__class__.instances.append(weakref.proxy(self))
        self.name = 'opsdroid'
        self.sys_status = 0
        self.connectors = []
        self.skills = []
        logging.info("Created main opsdroid object")

    def exit(self):
        """ Exit application """
        logging.info("Exiting application with return code " + str(self.sys_status))
        sys.exit(self.sys_status)

    def critical(self, error, code):
        """ Exit due to unrecoverable error """
        self.sys_status = code
        logging.critical(error)
        print("Error: " + error)
        self.exit()

    def start_connectors(self, connectors):
        """ Start the connectors """
        if len(connectors) == 0:
            self.critical("All connectors failed to load", 1)
        for connector_module in connectors:
            for name, cls in connector_module["module"].__dict__.items():
                if isinstance(cls, type) and "Connector" in name:
                    connector = cls(connector_module["config"])
                    self.connectors.append(connector)
                    connector.connect(self)

    def load_regex_skill(self, regex, skill):
        """ Load skills """
        self.skills.append({"regex": regex, "skill": skill})

    def parse(self, message):
        """ Parse a string against all skills """
        if message.text.strip() != "":
            logging.debug("Parsing input: " + message.text)
            for skill in self.skills:
                if "regex" in skill:
                    if self._match(skill["regex"], message.text):
                        skill["skill"](self, message)

    def _match(self, regex, message):
        """ Regex match a string """
        return re.match( regex, message, re.M|re.I)
