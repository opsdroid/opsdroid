"""A connector for Slack."""
import logging
import re

import slack
from emoji import demojize

from opsdroid.connector import Connector, register_event
from opsdroid.events import Message, Reaction
from opsdroid.connector.slack.events import Blocks


_LOGGER = logging.getLogger(__name__)


class ConnectorSlack(Connector):
    """A connector for Slack."""

    def __init__(self, config, opsdroid=None):
        """Create the connector."""
        super().__init__(config, opsdroid=opsdroid)
        _LOGGER.debug("Starting Slack connector")
        self.name = "slack"
        self.default_target = config.get("default-room", "#general")
        self.icon_emoji = config.get("icon-emoji", ":robot_face:")
        self.token = config["api-token"]
        self.timeout = config.get("connect-timeout", 10)
        self.slack = slack.WebClient(token=self.token, run_async=True)
        self.slack_rtm = slack.RTMClient(token=self.token, run_async=True)
        self.websocket = None
        self.bot_name = config.get("bot-name", "opsdroid")
        self.auth_info = None
        self.user_info = None
        self.bot_id = None
        self.known_users = {}
        self.keepalive = None
        self.reconnecting = False
        self.listening = True
        self._message_id = 0

        # Register callbacks
        slack.RTMClient.on(event="message", callback=self.process_message)

    async def connect(self):
        """Connect to the chat service."""
        _LOGGER.info("Connecting to Slack")

        try:
            # The slack library recommends you call `self.slack_rtm.start()`` here but it
            # seems to mess with the event loop's signal handlers which breaks opsdroid.
            # Therefore we need to directly call the private `_connect_and_read` method
            # instead. This method also blocks so we need to dispatch it to the loop as a task.
            self.opsdroid.eventloop.create_task(self.slack_rtm._connect_and_read())

            self.auth_info = (await self.slack.api_call("auth.test")).data
            self.user_info = (
                await self.slack.api_call(
                    "users.info",
                    http_verb="GET",
                    params={"user": self.auth_info["user_id"]},
                )
            ).data
            self.bot_id = self.user_info["user"]["profile"]["bot_id"]

            _LOGGER.debug("Connected as %s", self.bot_name)
            _LOGGER.debug("Using icon %s", self.icon_emoji)
            _LOGGER.debug("Default room is %s", self.default_target)
            _LOGGER.info("Connected successfully")
        except slack.errors.SlackApiError as error:
            _LOGGER.error(
                "Unable to connect to Slack due to %s - "
                "The Slack Connector will not be available.",
                error,
            )
        except Exception:
            await self.disconnect()
            raise

    async def disconnect(self):
        """Disconnect from Slack."""
        await self.slack_rtm.stop()
        self.listening = False

    async def listen(self):
        """Listen for and parse new messages."""

    async def process_message(self, **payload):
        """Process a raw message and pass it to the parser."""
        message = payload["data"]

        # Ignore own messages
        if (
            "subtype" in message
            and message["subtype"] == "bot_message"
            and message["bot_id"] == self.bot_id
        ):
            return

        # Lookup username
        _LOGGER.debug("Looking up sender username")
        try:
            user_info = await self.lookup_username(message["user"])
        except ValueError:
            return

        # Replace usernames in the message
        _LOGGER.debug("Replacing userids in message with usernames")
        message["text"] = await self.replace_usernames(message["text"])

        await self.opsdroid.parse(
            Message(
                message["text"],
                user_info["name"],
                message["channel"],
                self,
                raw_event=message,
            )
        )

    @register_event(Message)
    async def send_message(self, message):
        """Respond with a message."""
        _LOGGER.debug("Responding with: '%s' in room  %s", message.text, message.target)
        await self.slack.api_call(
            "chat.postMessage",
            json={
                "channel": message.target,
                "text": message.text,
                "as_user": False,
                "username": self.bot_name,
                "icon_emoji": self.icon_emoji,
            },
        )

    @register_event(Blocks)
    async def send_blocks(self, blocks):
        """Respond with structured blocks."""
        _LOGGER.debug("Responding with interactive blocks in room  %s", blocks.target)
        await self.slack.api_call(
            "chat.postMessage",
            json={
                "channel": blocks.target,
                "username": self.bot_name,
                "blocks": blocks.blocks,
                "icon_emoji": self.icon_emoji,
            },
        )

    @register_event(Reaction)
    async def send_reaction(self, reaction):
        """React to a message."""
        emoji = demojize(reaction.emoji).replace(":", "")
        _LOGGER.debug("Reacting with: %s", emoji)
        try:
            await self.slack.api_call(
                "reactions.add",
                json={
                    "name": emoji,
                    "channel": reaction.target,
                    "timestamp": reaction.linked_event.raw_event["ts"],
                },
            )
        except slack.errors.SlackApiError as error:
            if "invalid_name" in str(error):
                _LOGGER.warning("Slack does not support the emoji %s", emoji)
            else:
                raise

    async def lookup_username(self, userid):
        """Lookup a username and cache it."""
        if userid in self.known_users:
            user_info = self.known_users[userid]
        else:
            response = await self.slack.users_info(user=userid)
            user_info = response.data["user"]
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
            message = message.replace(
                "<@{userid}>".format(userid=userid), user_info["name"]
            )
        return message
