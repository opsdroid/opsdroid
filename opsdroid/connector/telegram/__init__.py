"""A connector for Telegram"""
import asyncio
import logging
import aiohttp


from opsdroid.connector import Connector
from opsdroid.message import Message


_LOGGER = logging.getLogger(__name__)


class ConnectorTelegram(Connector):
    """A connector the the char service Telegram."""

    def __init__(self, config):
        """Setup the connector.

        Args:
            config (dict): configuration settings from the
                file config.yaml.

        """
        _LOGGER.debug("Loaded telegram connector")
        super().__init__(config)
        self.name = "telegram"
        self.token = config["token"]
        self.latest_update = None
        self.default_room = None
        self.whitelisted_users = config.get("whitelisted_users", None)
        self.update_interval = config.get("update_interval", 0.5)

    def build_url(self, method):
        """Build the url to connect to the API.

        Args:
            methods (string): API call end point.

        Return:
            String that represents the full API url.

        """
        return "https://api.telegram.org/bot{}/{}".format(self.token, method)

    async def connect(self, opsdroid):
        """Connect to Telegram.

        Args:
            opsdroid (OpsDroid): An instance of opsdroid core.

        """
        _LOGGER.debug("Connecting to telegram")
        async with aiohttp.ClientSession() as session:
            async with session.get(self.build_url("getMe")) as resp:
                if resp.status != 200:
                    _LOGGER.error("Unable to connect")
                    _LOGGER.error("Telegram error %s, %s",
                                  resp.status, resp.text)
                else:
                    json = await resp.json()
                    _LOGGER.debug(json)
                    _LOGGER.debug("Connected to telegram as %s",
                                  json["result"]["username"])

    async def listen(self, opsdroid):
        """Listen for and parse new messages.

        Args:
            opsdroid (OpsDroid): An instance of opsdroid core.

        """
        while True:
            async with aiohttp.ClientSession() as session:
                data = {}
                if self.latest_update is not None:
                    data["offset"] = self.latest_update
                async with session.post(self.build_url("getUpdates"),
                                        data=data) as resp:
                    if resp.status != 200:
                        _LOGGER.error("Telegram error %s, %s",
                                      resp.status, resp.text)
                        break
                    else:
                        json = await resp.json()
                        _LOGGER.debug(json)
                        if len(json["result"]) > 0:
                            _LOGGER.debug("Received %i messages from telegram",
                                          len(json["result"]))
                        for response in json["result"]:
                            _LOGGER.debug(response)
                            if self.latest_update is None or \
                                    self.latest_update <= response["update_id"]:
                                self.latest_update = response["update_id"] + 1
                            if "text" in response["message"]:
                                if response["message"]["from"]["username"] == self.config.get("default_user", None):
                                    self.default_room = response["message"]["chat"]["id"]
                                message = Message(response["message"]["text"],
                                                  response["message"]["from"]["username"],
                                                  response["message"]["chat"],
                                                  self)
                                if self.whitelisted_users is None or \
                                        response["message"]["from"]["username"] in self.whitelisted_users:
                                    await opsdroid.parse(message)
                                else:
                                    message.text = "Sorry you're not allowed to speak with this bot"
                                    await self.respond(message)

                    await asyncio.sleep(self.update_interval)

    async def respond(self, message, room=None):
        """Respond with a message.

        Args:
            message (object): An instance of Message.
            room (string, optional): Name of the room to respond to.

        """
        _LOGGER.debug("Responding with: %s", message.text)

        async with aiohttp.ClientSession() as session:
            data = {}
            data["chat_id"] = message.room["id"]
            data["text"] = message.text
            async with session.post(self.build_url("sendMessage"),
                                    data=data) as resp:
                if resp.status == 200:
                    _LOGGER.debug("Successfully responded")
                else:
                    _LOGGER.error("Unable to responded")
