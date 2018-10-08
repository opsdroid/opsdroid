"""A connector for Telegram."""
import asyncio
import logging
import aiohttp


from opsdroid.connector import Connector
from opsdroid.message import Message


_LOGGER = logging.getLogger(__name__)


class ConnectorTelegram(Connector):
    """A connector the the char service Telegram."""

    def __init__(self, config):
        """Create the connector.

        Args:
            config (dict): configuration settings from the
                file config.yaml.

        """
        _LOGGER.debug("Loaded telegram connector")
        super().__init__(config)
        self.name = "telegram"
        self.latest_update = None
        self.default_room = None
        self.listening = True
        self.default_user = config.get("default-user", None)
        self.whitelisted_users = config.get("whitelisted-users", None)
        self.update_interval = config.get("update_interval", 1)

        try:
            self.token = config["token"]
        except (KeyError, AttributeError):
            _LOGGER.error("Unable to login: Access token is missing. "
                          "Telegram connector will be unavailable.")

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

        This method is not an authorization call. It basically
        checks if the API token was provided and makes an API
        call to Telegram and evaluates the status of the call.

        Args:
            opsdroid (OpsDroid): An instance of opsdroid core.

        """
        _LOGGER.debug("Connecting to telegram")
        async with aiohttp.ClientSession() as session:
            resp = await session.get(self.build_url("getMe"))

            if resp.status != 200:
                _LOGGER.error("Unable to connect")
                _LOGGER.error("Telegram error %s, %s",
                              resp.status, resp.text)
            else:
                json = await resp.json()
                _LOGGER.debug(json)
                _LOGGER.debug("Connected to telegram as %s",
                              json["result"]["username"])

    async def _parse_message(self, opsdroid, response):
        """Handle logic to parse a received message.

        Since everyone can send a private message to any user/bot
        in Telegram, this method allows to set a list of whitelisted
        users that can interact with the bot. If any other user tries
        to interact with the bot the command is not parsed and instead
        the bot will inform that user that he is not allowed to talk
        with the bot.

        We also set self.latest_update to +1 in order to get the next
        available message (or an empty {} if no message has been received
        yet) with the method self._get_messages().

        Args:
            opsdroid (OpsDroid): An instance of opsdroid core.
            response (dict): Response returned by aiohttp.ClientSession.
        """
        for response in response["result"]:
            _LOGGER.debug(response)
            if response["message"]["text"]:
                user = response["message"]["from"]["username"]

                message = Message(
                    response["message"]["text"],
                    user,
                    response["message"]["chat"],
                    self)

                if not self.whitelisted_users or \
                        user in self.whitelisted_users:
                    await opsdroid.parse(message)
                else:
                    message.text = "Sorry, you're not allowed " \
                                   "to speak with this bot."
                    await self.respond(message)
                self.latest_update = response["update_id"] + 1

    async def _get_messages(self, opsdroid):
        """Connect to the Telegram API.

        Uses an aiohttp ClientSession to connect to Telegram API
        and get the latest messages from the chat service.

        The data["offset"] is used to consume every new message, the API
        returns an  int - "update_id" value. In order to get the next
        message this value needs to be increased by 1 the next time
        the API is called. If no new messages exists the API will just
        return an empty {}.

        Args:
            opsdroid (OpsDroid): An instance of opsdroid core.

        """
        async with aiohttp.ClientSession() as session:
            data = {}
            if self.latest_update is not None:
                data["offset"] = self.latest_update
            resp = await session.get(self.build_url("getUpdates"),
                                     params=data)
            if resp.status != 200:
                _LOGGER.error("Telegram error %s, %s",
                              resp.status, resp.text)
                self.listening = False

            else:
                json = await resp.json()
                # _LOGGER.debug(json)

                await self._parse_message(opsdroid, json)

    async def listen(self, opsdroid):
        """Listen for and parse new messages.

        The bot will always listen to all opened chat windows,
        as long as opsdroid is running. Since anyone can start
        a new chat with the bot is recommended that a list of
        users to be whitelisted be provided in config.yaml.

        The method will sleep asynchronously at the end of
        every loop. The time can either be specified in the
        config.yaml with the param update-interval - this
        defaults to 1 second.

        Args:
            opsdroid (OpsDroid): An instance of opsdroid core.

        """
        while self.listening:
            await self._get_messages(opsdroid)

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
            resp = await session.post(self.build_url("sendMessage"),
                                      data=data)
            if resp.status == 200:
                _LOGGER.debug("Successfully responded")
            else:
                _LOGGER.error("Unable to respond.")
