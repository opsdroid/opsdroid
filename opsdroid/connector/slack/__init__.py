"""A connector for Slack."""
import logging
import asyncio
import json
import re

import aiohttp
import websockets
import slacker
from aioslacker import Slacker
from emoji import demojize

from opsdroid.connector import Connector, register_event
from opsdroid.events import Message, Reaction


_LOGGER = logging.getLogger(__name__)


class ConnectorSlack(Connector):
    """A connector for Slack."""

    def __init__(self, config, opsdroid=None):
        """Create the connector."""
        super().__init__(config, opsdroid=opsdroid)
        _LOGGER.debug("Starting Slack connector")
        self.name = "slack"
        self.default_target = config.get("default-room", "#general")
        self.icon_emoji = config.get("icon-emoji", ':robot_face:')
        self.token = config["api-token"]
        self.timeout = config.get("connect-timeout", 10)
        self.slacker = Slacker(token=self.token, timeout=self.timeout)
        self.websocket = None
        self.bot_name = config.get("bot-name", 'opsdroid')
        self.known_users = {}
        self.keepalive = None
        self.reconnecting = False
        self.listening = True
        self._message_id = 0

    async def connect(self):
        """Connect to the chat service."""
        _LOGGER.info("Connecting to Slack")

        try:
            connection = await self.slacker.rtm.start()
            self.websocket = await websockets.connect(connection.body['url'])

            _LOGGER.debug("Connected as %s", self.bot_name)
            _LOGGER.debug("Using icon %s", self.icon_emoji)
            _LOGGER.debug("Default room is %s", self.default_target)
            _LOGGER.info("Connected successfully")

            if self.keepalive is None or self.keepalive.done():
                self.keepalive = self.opsdroid.eventloop.create_task(
                    self.keepalive_websocket())
        except aiohttp.ClientOSError as error:
            _LOGGER.error(error)
            _LOGGER.error("Failed to connect to Slack, retrying in 10")
            await self.reconnect(10)
        except slacker.Error as error:
            _LOGGER.error("Unable to connect to Slack due to %s - "
                          "The Slack Connector will not be available.", error)
        except Exception:
            await self.disconnect()
            raise

    async def reconnect(self, delay=None):
        """Reconnect to the websocket."""
        try:
            self.reconnecting = True
            if delay is not None:
                await asyncio.sleep(delay)
            await self.connect()
        finally:
            self.reconnecting = False

    async def disconnect(self):
        """Disconnect from Slack."""
        await self.slacker.close()

    async def listen(self):
        """Listen for and parse new messages."""
        while self.listening:
            try:
                await self.receive_from_websocket()
            except AttributeError:
                break

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
                                              self,
                                              raw_event=message))

    @register_event(Message)
    async def send_message(self, message):
        """Respond with a message."""
        _LOGGER.debug("Responding with: '%s' in room  %s",
                      message.text, message.target)
        await self.slacker.chat.post_message(message.target,
                                             message.text,
                                             as_user=False,
                                             username=self.bot_name,
                                             icon_emoji=self.icon_emoji)

    @register_event(Reaction)
    async def send_reaction(self, reaction):
        """React to a message."""
        emoji = demojize(reaction.emoji)
        _LOGGER.debug("Reacting with: %s", emoji)
        try:
            await self.slacker.reactions.post('reactions.add', data={
                'name': emoji,
                'channel': reaction.target,
                'timestamp': reaction.linked_event.raw_event['ts']
            })
        except slacker.Error as error:
            if str(error) == 'invalid_name':
                _LOGGER.warning('Slack does not support the emoji %s', emoji)
            else:
                raise

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
