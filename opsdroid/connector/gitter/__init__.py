"""A connector for Gitter."""
import logging
import aiohttp
import asyncio
import json
import urllib
from voluptuous import Required

from opsdroid.connector import Connector, register_event
from opsdroid.events import Message

_LOGGER = logging.getLogger(__name__)
GITTER_STREAM_API = "https://stream.gitter.im/v1/rooms"
GITTER_MESSAGE_BASE_API = "https://api.gitter.im/v1/rooms"
CURRENT_USER_API = "https://api.gitter.im/v1/user/me"
CONFIG_SCHEMA = {Required("token"): str, Required("room-id"): str, "bot-name": str}


class ConnectorGitter(Connector):
    """A connector for Gitter."""

    def __init__(self, config, opsdroid=None):
        """Create the connector."""
        super().__init__(config, opsdroid=opsdroid)
        _LOGGER.debug(_("Starting Gitter Connector."))
        self.name = "gitter"
        self.bot_name = None  # set at connection time
        self.session = None
        self.response = None
        self.room_id = self.config.get("room-id")
        self.access_token = self.config.get("token")
        self.update_interval = 1
        self.opsdroid = opsdroid
        self.listening = True

    async def connect(self):
        """Create the connection."""

        # Create connection object with chat library

        _LOGGER.debug(_("Connecting with Gitter stream."))
        self.session = aiohttp.ClientSession()

        # Gitter figures out who we are based on just our access token, but we
        # need to additionally know our own user ID in order to know which
        # messages comes from us.
        current_user_url = self.build_url(
            CURRENT_USER_API,
            access_token=self.access_token,
        )
        response = await self.session.get(current_user_url, timeout=None)
        # We cannot continue without a user ID, so raise if this failed.
        response.raise_for_status()
        response_json = await response.json()
        self.bot_gitter_id = response_json["id"]
        self.bot_name = response_json["username"]
        _LOGGER.debug(
            _("Successfully obtained bot's gitter id, %s."), self.bot_gitter_id
        )

        message_stream_url = self.build_url(
            GITTER_STREAM_API,
            self.room_id,
            "chatMessages",
            access_token=self.access_token,
        )
        self.response = await self.session.get(message_stream_url, timeout=None)
        self.response.raise_for_status()

    def build_url(self, base_url, *res, **params):
        """Build the url. args ex:(base_url,p1,p2=1,p2=2)."""

        url = base_url
        for r in res:
            url = "{}/{}".format(url, r)
        if params:
            url = "{}?{}".format(url, urllib.parse.urlencode(params))
        return url

    async def listen(self):
        """Keep listing to the gitter channel."""
        _LOGGER.debug(_("Listening with Gitter stream."))
        while self.listening:
            try:
                await self._get_messages()
            except AttributeError:
                break

    async def _get_messages(self):
        """Message listener."""
        await asyncio.sleep(self.update_interval)
        async for data in self.response.content.iter_chunked(1024):
            message = await self.parse_message(data)
            # Do not parse messages that we ourselves sent.
            if message is not None and message.user_id != self.bot_gitter_id:
                await self.opsdroid.parse(message)

    async def parse_message(self, message):
        """Parse response from gitter to send message."""
        message = message.decode("utf-8").rstrip("\r\n")
        if len(message) > 1:
            message = json.loads(message)
            _LOGGER.debug(message)
            try:
                return Message(
                    text=message["text"],
                    user=message["fromUser"]["username"],
                    user_id=message["fromUser"]["id"],
                    target=self.room_id,
                    connector=self,
                )
            except KeyError as err:
                _LOGGER.error(_("Unable to parse message %r."), err)

    @register_event(Message)
    async def send_message(self, message):
        """Received parsed message and send it back to gitter room."""
        # Send message.text back to the chat service
        url = self.build_url(GITTER_MESSAGE_BASE_API, message.target, "chatMessages")
        headers = {
            "Authorization": "Bearer " + self.access_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {"text": message.text}
        resp = await self.session.post(url, json=payload, headers=headers)
        if resp.status == 200:
            _LOGGER.info(_("Successfully responded."))
        else:
            _LOGGER.error(_("Unable to respond."))

    async def disconnect(self):
        """Disconnect the gitter."""
        # Disconnect from the chat service
        self.listening = False
        await self.session.close()
