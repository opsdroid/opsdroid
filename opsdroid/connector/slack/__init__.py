"""A connector for Slack."""
import logging
import asyncio
import json
import re

import aiohttp
import websockets
from slacker import Slacker

from opsdroid.connector import Connector
from opsdroid.message import Message


_LOGGER = logging.getLogger(__name__)


class ConnectorSlack(Connector):
    """A connector for Slack."""

    def __init__(self, config):
        """Create the connector."""
        super().__init__(config)
        _LOGGER.debug("Starting Slack connector")
        self.name = "slack"
        self.config = config
        self.opsdroid = None
        self.default_room = config.get("default-room", "#general")
        self.icon_emoji = config.get("icon-emoji", ':robot_face:')
        self.token = config["api-token"]
        self.slacker = Slacker(self.token)
        self.websocket = None
        self.bot_name = config.get("bot-name", 'opsdroid')
        self.known_users = {}
        self.keepalive = None
        self.reconnecting = False
        self.listening = True
        self._message_id = 0

    async def connect(self, opsdroid=None):
        """Connect to the chat service."""
        if opsdroid is not None:
            self.opsdroid = opsdroid

        _LOGGER.info("Connecting to Slack")

        try:
            connection = await self.slacker.rtm.start()
            self.websocket = await websockets.connect(connection.body['url'])

            _LOGGER.debug("Connected as %s", self.bot_name)
            _LOGGER.debug("Using icon %s", self.icon_emoji)
            _LOGGER.debug("Default room is %s", self.default_room)
            _LOGGER.info("Connected successfully")

            if self.keepalive is None or self.keepalive.done():
                self.keepalive = self.opsdroid.eventloop.create_task(
                    self.keepalive_websocket())
        except aiohttp.ClientOSError as error:
            _LOGGER.error(error)
            _LOGGER.error("Failed to connect to Slack, retrying in 10")
            await self.reconnect(10)

    async def reconnect(self, delay=None):
        """Reconnect to the websocket."""
        try:
            self.reconnecting = True
            if delay is not None:
                await asyncio.sleep(delay)
            await self.connect()
        finally:
            self.reconnecting = False

    async def listen(self, opsdroid):
        """Listen for and parse new messages."""
        while self.listening:
            await self.receive_from_websocket()

    async def receive_from_websocket(self):
        """Get the next message from the websocket."""
        try:
            content = await self.websocket.recv()
            await self.process_message(json.loads(content))
        except websockets.exceptions.ConnectionClosed:
            _LOGGER.info("Slack websocket closed, reconnecting...")
            await self.reconnect(5)

    async def process_message(self, message):
        """Process a raw message and pass it to the parser."""
        if "type" in message and message["type"] == "message" and \
                "user" in message:

            # Ignore bot messages
            if "subtype" in message and \
                    message["subtype"] == "bot_message":
                return

            # Lookup username
            _LOGGER.debug("Looking up sender username")
            try:
                user_info = await self.lookup_username(message["user"])
            except ValueError:
                return

            # Replace usernames in the message
            _LOGGER.debug("Replacing userids in message with usernames")
            message["text"] = await self.replace_usernames(
                message["text"])

            await self.opsdroid.parse(Message(message["text"],
                                              user_info["name"],
                                              message["channel"],
                                              self))

    async def respond(self, message, room=None):
        """Respond with a message."""
        _LOGGER.debug("Responding with: '" + message.text +
                      "' in room " + message.room)
        await self.slacker.chat.post_message(message.room,
                                             message.text,
                                             as_user=False,
                                             username=self.bot_name,
                                             icon_emoji=self.icon_emoji)

    async def keepalive_websocket(self):
        """Keep pinging the websocket to keep it alive."""
        while self.listening:
            await self.ping_websocket()

    async def ping_websocket(self):
        """Ping the websocket."""
        await asyncio.sleep(60)
        self._message_id += 1
        try:
            await self.websocket.send(
                json.dumps({'id': self._message_id, 'type': 'ping'}))
        except (websockets.exceptions.InvalidState,
                websockets.exceptions.ConnectionClosed,
                aiohttp.ClientOSError,
                TimeoutError):
            _LOGGER.info("Slack websocket closed, reconnecting...")
            if not self.reconnecting:
                await self.reconnect()

    async def lookup_username(self, userid):
        """Lookup a username and cache it."""
        if userid in self.known_users:
            user_info = self.known_users[userid]
        else:
            response = await self.slacker.users.info(userid)
            user_info = response.body["user"]
            if isinstance(user_info, dict):
                self.known_users[userid] = user_info
            else:
                raise ValueError("Returned user is not a dict.")
        return user_info

    async def replace_usernames(self, message):
        """Replace User ID with username in message text."""
        userids = re.findall(r"\<\@([A-Z0-9]+)(?:\|.+)?\>", message)
        for userid in userids:
            user_info = await self.lookup_username(userid)
            message = message.replace("<@{userid}>".format(userid=userid),
                                      user_info["name"])
        return message
