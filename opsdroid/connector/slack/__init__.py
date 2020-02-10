"""A connector for Slack."""
import logging
import os
import ssl
import certifi
import asyncio
import json
import re

import aiohttp
import websockets
from emoji import demojize
from voluptuous import Required

from opsdroid.connector import Connector, register_event
import opsdroid.events
from opsdroid.connector.slack.events import Blocks, SlackEventCreator


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
        self._event_creator = SlackEventCreator(self)

    async def get_user_id(self):
        if self._user_id:
            return self._user_id

        auth = await self.slacker.auth.test()
        self._user_id = auth.body["user_id"]

        return self._user_id

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
            connection = await self.slacker.rtm.start()
            self.websocket = await websockets.connect(connection.body["url"])

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
        self.slack_rtm.stop()
        self.listening = False

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
        if "type" in message:
            if "user" in message:
                # Ignore messages that come from us
                self_id = await self.get_user_id()
                if message["user"] == self_id:
                    return

            _LOGGER.debug(f"Processing event with content {message}")
            event = await self._event_creator.create_event(
                message, message.get("channel")
            )
            await self.opsdroid.parse(event)

    @register_event(opsdroid.events.Message)
    async def _send_message(self, message):
        """Respond with a message."""
        _LOGGER.debug("Responding with: '%s' in room  %s", message.text, message.target)
        await self.slacker.chat.post_message(
            message.target,
            message.text,
            as_user=False,
            username=self.bot_name,
            icon_emoji=self.icon_emoji,
        )

    @register_event(Blocks)
    async def _send_blocks(self, blocks):
        """Respond with structured blocks."""
        _LOGGER.debug("Responding with interactive blocks in room  %s", blocks.target)
        await self.slacker.chat.post(
            "chat.postMessage",
            data={
                "channel": blocks.target,
                "username": self.bot_name,
                "blocks": blocks.blocks,
                "icon_emoji": self.icon_emoji,
            },
        )

    @register_event(opsdroid.events.Reaction)
    async def send_reaction(self, reaction):
        """React to a message."""
        emoji = demojize(reaction.emoji).replace(":", "")
        _LOGGER.debug("Reacting with: %s", emoji)
        try:
            await self.slacker.reactions.post(
                "reactions.add",
                data={
                    "name": emoji,
                    "channel": reaction.target,
                    "timestamp": reaction.linked_event.raw_event["ts"],
                },
            )
        except slack.errors.SlackApiError as error:
            if "invalid_name" in str(error):
                _LOGGER.warning(_("Slack does not support the emoji %s."), emoji)
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
                json.dumps({"id": self._message_id, "type": "ping"})
            )
        except (
            websockets.exceptions.InvalidState,
            websockets.exceptions.ConnectionClosed,
            aiohttp.ClientOSError,
            TimeoutError,
        ):
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
        params = creation_event.room_params
        params = params.get("slack", params)
        resp = await self.slacker.channels.create(creation_event.name)
        return resp.body["channel"]["id"]

    @register_event(opsdroid.events.RoomName)
    async def _send_room_name_set(self, name_event):
        return await self.slacker.channels.rename(
            name_event.target, name_event.name, "true"
        )

    @register_event(opsdroid.events.JoinRoom)
    async def _send_join_room(self, join_event):
        return await self.slacker.channels.join(join_event.target, "true")

    @register_event(opsdroid.events.UserInvite)
    async def _send_user_invitation(self, invite_event):
        return await self.slacker.channels.invite(
            invite_event.target, invite_event.user
        )

    @register_event(opsdroid.events.RoomDescription)
    async def _send_room_desciption(self, desc_event):
        return await self.slacker.channels.set_topic(
            desc_event.target, desc_event.description
        )
