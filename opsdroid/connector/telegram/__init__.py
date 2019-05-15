"""A connector for Telegram."""
import asyncio
import logging
import aiohttp

from opsdroid.connector import Connector, register_event
from opsdroid.events import Message, Image


_LOGGER = logging.getLogger(__name__)


class ConnectorTelegram(Connector):
    """A connector the the char service Telegram."""

    def __init__(self, config, opsdroid=None):
        """Create the connector.

        Args:
            config (dict): configuration settings from the
                file config.yaml.

        """
        _LOGGER.debug("Loaded telegram connector")
        super().__init__(config, opsdroid=opsdroid)
        self.name = "telegram"
        self.opsdroid = opsdroid
        self.latest_update = None
        self.default_target = None
        self.listening = True
        self.default_user = config.get("default-user", None)
        self.whitelisted_users = config.get("whitelisted-users", None)
        self.update_interval = config.get("update_interval", 1)
        self.session = None
        self._closing = asyncio.Event()
        self.loop = asyncio.get_event_loop()

        try:
            self.token = config["token"]
        except (KeyError, AttributeError):
            _LOGGER.error("Unable to login: Access token is missing. "
                          "Telegram connector will be unavailable.")

    @staticmethod
    def get_user(response):
        """Get user from response.

        The API response is different depending on how
        the bot is set up and where the message is coming
        from. This method was created to keep if/else
        statements to a minium on  _parse_message.

        Args:
            response (dict): Response returned by aiohttp.ClientSession.

        """
        user = None
        if "username" in response["message"]["from"]:
            user = response["message"]["from"]["username"]

        elif "first_name" in response["message"]["from"]:
            user = response["message"]["from"]["first_name"]

        return user

    def handle_user_permission(self, response, user):
        """Handle user permissions.

        This will check if the user that tried to talk with
        the bot is allowed to do so. It will also work with
        userid to improve security.

        """
        user_id = response["message"]["from"]["id"]

        if not self.whitelisted_users or \
            user in self.whitelisted_users or \
                user_id in self.whitelisted_users:
            return True

        return False

    def build_url(self, method):
        """Build the url to connect to the API.

        Args:
            method (string): API call end point.

        Return:
            String that represents the full API url.

        """
        return "https://api.telegram.org/bot{}/{}".format(self.token, method)

    async def delete_webhook(self):
        """Delete Telegram webhook.

        The Telegram api will thrown an 409 error when an webhook is
        active and a call to getUpdates is made. This method will
        try to request the deletion of the webhook to make the getUpdate
        request possible.

        """
        _LOGGER.debug("Sending deleteWebhook request to Telegram...")
        resp = await self.session.get(self.build_url("deleteWebhook"))

        if resp.status == 200:
            _LOGGER.debug("Telegram webhook deleted successfully.")
        else:
            _LOGGER.debug("Unable to delete webhook.")

    async def connect(self):
        """Connect to Telegram.

        This method is not an authorization call. It basically
        checks if the API token was provided and makes an API
        call to Telegram and evaluates the status of the call.

        """
        _LOGGER.debug("Connecting to telegram")
        self.session = aiohttp.ClientSession()
        resp = await self.session.get(self.build_url("getMe"))

        if resp.status != 200:
            _LOGGER.error("Unable to connect")
            _LOGGER.error("Telegram error %s, %s",
                          resp.status, resp.text)
        else:
            json = await resp.json()
            _LOGGER.debug(json)
            _LOGGER.debug("Connected to telegram as %s",
                          json["result"]["username"])

    async def _parse_message(self, response):
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
            response (dict): Response returned by aiohttp.ClientSession.

        """
        for result in response["result"]:
            _LOGGER.debug(result)
            if result.get('edited_message', None):
                result['message'] = result.pop('edited_message')
            if "channel" in result["message"]["chat"]["type"]:
                _LOGGER.debug("Channel message parsing not supported "
                              "- Ignoring message")
            elif "message" in result and "text" in result["message"]:
                user = self.get_user(result)
                message = Message(
                    result["message"]["text"],
                    user,
                    result["message"]["chat"],
                    self)

                if self.handle_user_permission(result, user):
                    await self.opsdroid.parse(message)
                else:
                    message.text = "Sorry, you're not allowed " \
                                   "to speak with this bot."
                    await self.send(message)
                self.latest_update = result["update_id"] + 1
            else:
                _LOGGER.error("Unable to parse the message.")

    async def _get_messages(self):
        """Connect to the Telegram API.

        Uses an aiohttp ClientSession to connect to Telegram API
        and get the latest messages from the chat service.

        The data["offset"] is used to consume every new message, the API
        returns an  int - "update_id" value. In order to get the next
        message this value needs to be increased by 1 the next time
        the API is called. If no new messages exists the API will just
        return an empty {}.

        """
        data = {}
        if self.latest_update is not None:
            data["offset"] = self.latest_update

        await asyncio.sleep(self.update_interval)
        resp = await self.session.get(self.build_url("getUpdates"),
                                      params=data)

        if resp.status == 409:
            _LOGGER.info("Can't get updates because previous "
                         "webhook is still active. Will try to "
                         "delete webhook.")
            await self.delete_webhook()

        if resp.status != 200:
            _LOGGER.error("Telegram error %s, %s",
                          resp.status, resp.text)
            self.listening = False
        else:
            json = await resp.json()

            await self._parse_message(json)

    async def get_messages_loop(self):
        """Listen for and parse new messages.

        The bot will always listen to all opened chat windows,
        as long as opsdroid is running. Since anyone can start
        a new chat with the bot is recommended that a list of
        users to be whitelisted be provided in config.yaml.

        The method will sleep asynchronously at the end of
        every loop. The time can either be specified in the
        config.yaml with the param update-interval - this
        defaults to 1 second.

        """
        while self.listening:
            await self._get_messages()

    async def listen(self):
        """Listen method of the connector.

        Every connector has to implement the listen method. When an
        infinite loop is running, it becomes hard to cancel this task.
        So we are creating a task and set it on a variable so we can
        cancel the task.

        """
        message_getter = self.loop.create_task(self.get_messages_loop())
        await self._closing.wait()
        message_getter.cancel()

    @register_event(Message)
    async def send_message(self, message):
        """Respond with a message.

        Args:
            message (object): An instance of Message.

        """
        _LOGGER.debug("Responding with: %s", message.text)

        data = dict()
        data["chat_id"] = message.target["id"]
        data["text"] = message.text
        resp = await self.session.post(self.build_url("sendMessage"),
                                       data=data)
        if resp.status == 200:
            _LOGGER.debug("Successfully responded")
        else:
            _LOGGER.error("Unable to respond.")

    @register_event(Image)
    async def send_image(self, file_event):
        """Send Image to Telegram.

        Gets the chat id from the channel and then
        sends the bytes of the image as multipart/form-data.

        """
        data = aiohttp.FormData()
        data.add_field('chat_id',
                       str(file_event.target["id"]),
                       content_type="multipart/form-data")
        data.add_field("photo",
                       await file_event.get_file_bytes(),
                       content_type="multipart/form-data")

        resp = await self.session.post(self.build_url("sendPhoto"),
                                       data=data)
        if resp.status == 200:
            _LOGGER.debug("Sent %s image "
                          "successfully", file_event.name)
        else:
            _LOGGER.debug("Unable to send image - "
                          "Status Code %s", resp.status)

    async def disconnect(self):
        """Disconnect from Telegram.

        Stops the infinite loop found in self._listen(), closes
        aiohttp session.

        """
        self.listening = False
        self._closing.set()
        await self.session.close()
