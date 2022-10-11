import json
import logging

from voluptuous import Required

from opsdroid.connector import Connector, register_event
from opsdroid.connector.facebook import CONFIG_SCHEMA
from opsdroid.events import Message

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = {
    Required("token") : str,
    Required("url"):str,
    "bot-name":str
}

class ConnectorDiscord(Connector):
    def __init__(self,config,opsdroid = None):
        super().__init__(config,opsdroid=opsdroid)
        self.name = config.get("name","discord")
        self.bot_name = config.get("bot-name","opsdroid")
        self.url = config["url"]
