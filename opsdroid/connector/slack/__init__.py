"""A connector for Slack."""
import logging
import re
import os
import ssl
import certifi
import json

import aiohttp

import slack
from emoji import demojize
from voluptuous import Required

from opsdroid.connector import Connector, register_event
from opsdroid.events import Message, Reaction
from opsdroid.connector.slack.events import (
    Blocks,
    BlockActions,
    MessageAction,
    ViewSubmission,
    ViewClosed,
)


_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = {
    Required("token"): str,
    "bot-name": str,
    "default-room": str,
    "icon-emoji": str,
    "connect-timeout": int,
    "chat-as-user": bool,
}


class ConnectorSlack(Connector):
    """A connector for Slack."""

    def __init__(self, config, opsdroid=None):
        """Create the connector."""
        super().__init__(config, opsdroid=opsdroid)
        _LOGGER.debug(_("Starting Slack connector."))
        self.name = "slack"
        self.default_target = config.get("default-room", "#general")
        self.icon_emoji = config.get("icon-emoji", ":robot_face:")
        self.token = config["token"]
        self.timeout = config.get("connect-timeout", 10)
        self.chat_as_user = config.get("chat-as-user", False)
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.slack = slack.WebClient(
            token=self.token,
            run_async=True,
            ssl=self.ssl_context,
            proxy=os.environ.get("HTTPS_PROXY"),
        )
        self.slack_rtm = slack.RTMClient(
            token=self.token,
            run_async=True,
            ssl=self.ssl_context,
            proxy=os.environ.get("HTTPS_PROXY"),
        )
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
        _LOGGER.info(_("Connecting to Slack."))

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

            self.opsdroid.web_server.web_app.router.add_post(
                "/connector/{}/interactions".format(self.name),
                self.slack_interactions_handler,
            )

            _LOGGER.debug(_("Connected as %s."), self.bot_name)
            _LOGGER.debug(_("Using icon %s."), self.icon_emoji)
            _LOGGER.debug(_("Default room is %s."), self.default_target)
            _LOGGER.info(_("Connected successfully."))
        except slack.errors.SlackApiError as error:
            _LOGGER.error(
                _(
                    "Unable to connect to Slack due to %s."
                    "The Slack Connector will not be available."
                ),
                error,
            )
        except Exception:
            await self.disconnect()
            raise

    async def disconnect(self):
        """Disconnect from Slack."""
        self.slack_rtm.stop()
        self.listening = False

    async def listen(self):
        """Listen for and parse new messages."""

    async def process_message(self, **payload):
        """Process a raw message and pass it to the parser."""
        message = payload["data"]

        # Ignore message edits
        if "subtype" in message and message["subtype"] == "message_changed":
            return

        # Ignore own messages
        if (
            "subtype" in message
            and message["subtype"] == "bot_message"
            and message["bot_id"] == self.bot_id
        ):
            return

        # Lookup username
        _LOGGER.debug(_("Looking up sender username."))
        try:
            user_info = await self.lookup_username(message["user"])
        except ValueError:
            return

        # Replace usernames in the message
        _LOGGER.debug(_("Replacing userids in message with usernames."))
        message["text"] = await self.replace_usernames(message["text"])

        await self.opsdroid.parse(
            Message(
                text=message["text"],
                user=user_info["name"],
                target=message["channel"],
                connector=self,
                raw_event=message,
            )
        )

    @register_event(Message)
    async def send_message(self, message):
        """Respond with a message."""
        _LOGGER.debug(
            _("Responding with: '%s' in room  %s."), message.text, message.target
        )
        await self.slack.api_call(
            "chat.postMessage",
            data={
                "channel": message.target,
                "text": message.text,
                "as_user": self.chat_as_user,
                "username": self.bot_name,
                "icon_emoji": self.icon_emoji,
            },
        )

    @register_event(Blocks)
    async def send_blocks(self, blocks):
        """Respond with structured blocks."""
        _LOGGER.debug(
            _("Responding with interactive blocks in room %s."), blocks.target
        )
        await self.slack.api_call(
            "chat.postMessage",
            data={
                "channel": blocks.target,
                "as_user": self.chat_as_user,
                "username": self.bot_name,
                "blocks": blocks.blocks,
                "icon_emoji": self.icon_emoji,
            },
        )

    @register_event(Reaction)
    async def send_reaction(self, reaction):
        """React to a message."""
        emoji = demojize(reaction.emoji).replace(":", "")
        _LOGGER.debug(_("Reacting with: %s."), emoji)
        try:
            await self.slack.api_call(
                "reactions.add",
                data={
                    "name": emoji,
                    "channel": reaction.target,
                    "timestamp": reaction.linked_event.event_id,
                },
            )
        except slack.errors.SlackApiError as error:
            if "invalid_name" in str(error):
                _LOGGER.warning(_("Slack does not support the emoji %s."), emoji)
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

    async def slack_interactions_handler(self, request):
        """Handle interactive events in Slack.

        For each entry in request, it will check if the entry is one of the four main
        interaction types in slack: block_actions, message_actions, view_submissions
        and view_closed. Then it will process all the incoming messages.

        Return:
            A 200 OK response. The Messenger Platform will resend the webhook
            event every 20 seconds, until a 200 OK response is received.
            Failing to return a 200 OK may cause your webhook to be
            unsubscribed by the Messenger Platform.

        """

        req_data = await request.post()
        payload = json.loads(req_data["payload"])

        if "type" in payload:
            if payload["type"] == "block_actions":
                for action in payload["actions"]:
                    block_action = BlockActions(
                        payload,
                        user=payload["user"]["id"],
                        target=payload["channel"]["id"],
                        connector=self,
                    )

                    action_value = None
                    if action["type"] == "button":
                        action_value = action["value"]
                    elif action["type"] in ["overflow", "static_select"]:
                        action_value = action["selected_option"]["value"]
                    elif action["type"] == "datepicker":
                        action_value = action["selected_date"]
                    elif action["type"] == "multi_static_select":
                        action_value = [v["value"] for v in action["selected_options"]]

                    if action_value:
                        await block_action.update_entity("value", action_value)
                    await self.opsdroid.parse(block_action)
            elif payload["type"] == "message_action":
                await self.opsdroid.parse(
                    MessageAction(
                        payload,
                        user=payload["user"]["id"],
                        target=payload["channel"]["id"],
                        connector=self,
                    )
                )
            elif payload["type"] == "view_submission":
                await self.opsdroid.parse(
                    ViewSubmission(
                        payload,
                        user=payload["user"]["id"],
                        target=payload["user"]["id"],
                        connector=self,
                    )
                )
            elif payload["type"] == "view_closed":
                await self.opsdroid.parse(
                    ViewClosed(
                        payload,
                        user=payload["user"]["id"],
                        target=payload["user"]["id"],
                        connector=self,
                    )
                )

        return aiohttp.web.Response(text=json.dumps("Received"), status=200)
