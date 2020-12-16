"""A connector for Slack."""
import re
import logging
import os
import ssl
import certifi
import json

import aiohttp

import slack
from emoji import demojize
from voluptuous import Required

from opsdroid.connector import Connector, register_event
import opsdroid.events
from opsdroid.connector.slack.events import (
    Blocks,
    EditedBlocks,
    BlockActions,
    MessageAction,
    ViewSubmission,
    ViewClosed,
    SlackEventCreator,
)


_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = {
    Required("token"): str,
    "user-token": str,
    "bot-name": str,
    "default-room": str,
    "icon-emoji": str,
    "connect-timeout": int,
    "chat-as-user": bool,
    "start_thread": bool,
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
        self.user_token = config.get("user-token")
        self.timeout = config.get("connect-timeout", 10)
        self.chat_as_user = config.get("chat-as-user", False)
        self.start_thread = config.get("start_thread", False)
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.slack = slack.WebClient(
            token=self.token,
            run_async=True,
            ssl=self.ssl_context,
            proxy=os.environ.get("HTTPS_PROXY"),
        )
        self.slack_user = slack.WebClient(
            token=self.user_token,
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

        self._event_creator = SlackEventCreator(self)

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

    @register_event(opsdroid.events.Message)
    async def _send_message(self, message):
        """Respond with a message."""
        _LOGGER.debug(
            _("Responding with: '%s' in room  %s."), message.text, message.target
        )
        data = {
            "channel": message.target,
            "text": message.text,
            "as_user": self.chat_as_user,
            "username": self.bot_name,
            "icon_emoji": self.icon_emoji,
        }

        if message.linked_event:
            if "thread_ts" in message.linked_event.raw_event:
                if (
                    message.linked_event.event_id
                    != message.linked_event.raw_event["thread_ts"]
                ):
                    # Linked Event is inside a thread
                    data["thread_ts"] = message.linked_event.raw_event["thread_ts"]
            elif self.start_thread:
                data["thread_ts"] = message.linked_event.event_id

        return await self.slack.api_call(
            "chat.postMessage",
            data=data,
        )

    @register_event(opsdroid.events.EditedMessage)
    async def _edit_message(self, message):
        """Edit a message."""
        _LOGGER.debug(
            _("Editing message with timestamp: '%s' to %s in room  %s."),
            message.linked_event,
            message.text,
            message.target,
        )
        data = {
            "channel": message.target,
            "ts": message.linked_event,
            "text": message.text,
            "as_user": self.chat_as_user,
        }

        return await self.slack.api_call(
            "chat.update",
            data=data,
        )

    @register_event(Blocks)
    async def _send_blocks(self, blocks):
        """Respond with structured blocks."""
        _LOGGER.debug(
            _("Responding with interactive blocks in room %s."), blocks.target
        )
        return await self.slack.api_call(
            "chat.postMessage",
            data={
                "channel": blocks.target,
                "as_user": self.chat_as_user,
                "username": self.bot_name,
                "blocks": blocks.blocks,
                "icon_emoji": self.icon_emoji,
            },
        )

    @register_event(EditedBlocks)
    async def _edit_blocks(self, blocks):
        """Edit a particular block."""
        _LOGGER.debug(
            _("Editing interactive blocks with timestamp: '%s' in room  %s."),
            blocks.linked_event,
            blocks.target,
        )
        data = {
            "channel": blocks.target,
            "ts": blocks.linked_event,
            "blocks": blocks.blocks,
            "as_user": self.chat_as_user,
        }

        return await self.slack.api_call(
            "chat.update",
            data=data,
        )

    @register_event(opsdroid.events.Reaction)
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
                        block_action.update_entity("value", action_value)
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

    @register_event(opsdroid.events.NewRoom)
    async def _send_room_creation(self, creation_event):
        _LOGGER.debug(_("Creating room %s."), creation_event.name)
        return await self.slack_user.api_call(
            "conversations.create", data={"name": creation_event.name}
        )

    @register_event(opsdroid.events.RoomName)
    async def _send_room_name_set(self, name_event):
        _LOGGER.debug(
            _("Renaming room %s to '%s'."), name_event.target, name_event.name
        )
        return await self.slack_user.api_call(
            "conversations.rename",
            data={"channel": name_event.target, "name": name_event.name},
        )

    @register_event(opsdroid.events.JoinRoom)
    async def _send_join_room(self, join_event):
        return await self.slack_user.api_call(
            "conversations.join", data={"channel": join_event.target}
        )

    @register_event(opsdroid.events.UserInvite)
    async def _send_user_invitation(self, invite_event):
        _LOGGER.debug(
            _("Inviting user %s to room '%s'."), invite_event.user, invite_event.target
        )
        return await self.slack_user.api_call(
            "conversations.invite",
            data={"channel": invite_event.target, "users": invite_event.user_id},
        )

    @register_event(opsdroid.events.RoomDescription)
    async def _send_room_desciption(self, desc_event):
        return await self.slack_user.api_call(
            "conversations.setTopic",
            data={"channel": desc_event.target, "topic": desc_event.description},
        )

    @register_event(opsdroid.events.PinMessage)
    async def _send_pin_message(self, pin_event):
        return await self.slack.api_call(
            "pins.add",
            data={
                "channel": pin_event.target,
                "timestamp": pin_event.linked_event.event_id,
            },
        )

    @register_event(opsdroid.events.UnpinMessage)
    async def _send_unpin_message(self, unpin_event):
        return await self.slack.api_call(
            "pins.remove",
            data={
                "channel": unpin_event.target,
                "timestamp": unpin_event.linked_event.event_id,
            },
        )
