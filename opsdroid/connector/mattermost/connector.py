"""A connector for Mattermost."""
import logging
import json

from voluptuous import Required

from opsdroid.connector import Connector, register_event
from opsdroid.events import Message

from .driver import Driver

import asyncio

from enum import Enum

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = {
    Required("token"): str,
    Required("url"): str,
    Required("team-name"): str,
    "use-threads": bool,
    "scheme": str,
    "port": int,
    "connect-timeout": int,
    "emoji-trigger": str,
    "trigger-on-mention": bool,
}

DIRECT_MESSAGE_TYPE = "D"


class EventType(Enum):
    MESSAGE = 1
    REACTION = 2


class ConnectorMattermost(Connector):
    """A connector for Mattermost."""

    def __init__(self, config, opsdroid=None):
        """Create the connector."""
        super().__init__(config, opsdroid=opsdroid)
        _LOGGER.debug(_("Starting Mattermost connector"))
        self.name = config.get("name", "mattermost")
        self._token = config["token"]
        self._url = config["url"]
        self._team_name = config["team-name"]
        self._scheme = config.get("scheme", "https")
        self._port = config.get("port", 8065)
        self._timeout = config.get("connect-timeout", 30)
        self._use_threads = config.get("use-threads", False)
        self._emoji_trigger = config.get("emoji-trigger", None)
        self._trigger_on_mention = config.get("trigger-on-mention", True)

        self._bot_id = None
        self._bot_name = None

        self._mm_driver = Driver(
            {
                "url": self._url,
                "token": self._token,
                "scheme": self._scheme,
                "port": self._port,
                "timeout": self._timeout,
            }
        )
        self._websocket = None

    async def connect(self):
        """Connect to the chat service. This does not include the Websocket!"""
        _LOGGER.info(_("Connecting to Mattermost"))

        await self._mm_driver.__aenter__()
        try:
            login_response = await self._mm_driver.connect()
        except Exception as ex:
            _LOGGER.error(_("Failed connecting to Mattermost '%s'"), ex)
            raise ex

        body = await login_response.json()
        _LOGGER.info(
            _("Mattermost responded with the identity of the token's user: '%s'"),
            repr(body),
        )

        if "id" not in body:
            raise ValueError(
                "Mattermost response must contain our own client ID. Otherwise OpsDroid would respond to itself indefinitely."
            )
        self._bot_id = body["id"]
        self._bot_name = body["username"]

        if "username" in body:
            _LOGGER.info(_("Connected as %s"), self._bot_name)

        _LOGGER.info(_("Connected successfully"))

    async def disconnect(self):
        """Disconnect from Mattermost."""
        await self._mm_driver.__aexit__(None, None, None)

    async def listen(self):
        """
        Listen for and parse new messages.
        This is only the Websocket and must be called after 'connect', since that initializes the driver/web client
        """
        self._websocket = self._mm_driver.init_websocket(self.process_message)
        await self._websocket

    async def process_message(self, raw_json_message):
        """Process a raw message and pass it to the parser."""
        _LOGGER.debug(
            _("Processing raw Mattermost message: '%s'"), repr(raw_json_message)
        )

        if "event" in raw_json_message and raw_json_message["event"] == "posted":
            data = raw_json_message["data"]
            post = json.loads(data["post"])

            await self.process_mattermost_post(
                event_type=EventType.MESSAGE,
                message=post["message"],
                user_name=data["sender_name"],
                user_id=post["user_id"],
                channel_name=data["channel_name"],
                channel_type=data["channel_type"],
                reactions=[],  # message was just now created, no reactions yet
                raw_json_message=raw_json_message,
            )
        elif (
            self._emoji_trigger
            and "event" in raw_json_message
            and raw_json_message["event"] == "reaction_added"
        ):
            data = raw_json_message["data"]
            reaction = json.loads(data["reaction"])
            if reaction["emoji_name"] == self._emoji_trigger:
                # This is the emoji we've been waiting for
                # retrieve the post ID
                post_id = reaction["post_id"]
                post_future = self._mm_driver.posts.create_future(
                    self._mm_driver.posts.get_post(post_id)
                )

                user_id = reaction["user_id"]
                user_future = self._mm_driver.users.create_future(
                    self._mm_driver.users.get_user(user_id)
                )

                channel_id = reaction["channel_id"]
                channel_future = self._mm_driver.channels.create_future(
                    self._mm_driver.channels.get_channel_by_id(channel_id)
                )

                # wait for all futures to complete
                await asyncio.gather(post_future, user_future, channel_future)

                # We need the raw post as well as the JSON
                raw_post = await post_future.result().text()
                post = json.loads(raw_post)

                channel = await channel_future.result().json()
                channel_name = channel["name"]

                user = await user_future.result().json()
                user_name = user["username"]

                message = post["message"]

                # The emoji reaction does not contain all the information about the post that we need later on
                # so we must create a new raw message with the post data
                raw_message = raw_json_message.copy()
                raw_message["data"]["post"] = raw_post

                await self.process_mattermost_post(
                    event_type=EventType.REACTION,
                    message=message,
                    user_name=user_name,
                    user_id=user_id,
                    channel_name=channel_name,
                    channel_type=channel["type"],
                    reactions=post["metadata"]["reactions"],
                    raw_json_message=raw_message,
                )

    async def process_mattermost_post(
        self,
        event_type: EventType,
        message: str,
        user_name: str,
        user_id: str,
        channel_name: str,
        channel_type: str,
        reactions: list,
        raw_json_message: dict,
    ):
        """Process a Mattermost post."""
        # if connected to Mattermost, don't parse our own messages
        if self._bot_id == user_id:
            _LOGGER.debug(_("I am the author: ignoring message"))
            return

        # if a message is not direct message, check if the bot has been mentioned
        if (
            event_type == EventType.MESSAGE
            and self._trigger_on_mention
            and channel_type != DIRECT_MESSAGE_TYPE
            and self._bot_name not in message
        ):
            _LOGGER.debug(
                _("Not a direct message and I am not mentioned: ignoring message")
            )
            return

        # if the emoji is not the first of its kind, ignore it
        if event_type == EventType.REACTION and self._emoji_trigger:
            # check if the emoji is the first of its kind
            reaction_count = 0
            for reaction in reactions:
                if reaction["emoji_name"] == self._emoji_trigger:
                    reaction_count += 1
            if reaction_count > 1:
                _LOGGER.debug(
                    _("Reaction is not the first of its kind: ignoring message")
                )
                return

        await self.opsdroid.parse(
            Message(
                text=message,
                user=user_name,
                target=channel_name,
                connector=self,
                raw_event=raw_json_message,
            )
        )

    @register_event(Message)
    async def send_message(self, message):
        """Respond with a message."""
        _LOGGER.debug(
            _("Responding with: '%s' in room  %s"), message.text, message.target
        )

        async with self._mm_driver.channels.get_channel_for_team_by_name(
            self._team_name, message.target
        ) as response:
            myjson = await response.json()
            channel_id = myjson["id"]

        body = {}
        if self._use_threads:
            data = message.linked_event.raw_event["data"]
            post = json.loads(data["post"])

            # root_id is set if it is already a thread
            # otherwise use the id to start a new thread from that top level message
            root_id = ("root_id" in post and post["root_id"]) or post["id"]

            body = {
                "channel_id": channel_id,
                "message": message.text,
                "root_id": root_id,
            }
        else:
            body = {"channel_id": channel_id, "message": message.text}

        async with self._mm_driver.posts.create_post(json=body) as response:
            _LOGGER.debug(
                _("Mattermost responds with status code '%s' to the new post"),
                response.status,
            )
