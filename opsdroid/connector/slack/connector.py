"""A connector for Slack."""

import asyncio
import json
import logging
import os
import re
import ssl
import time
import urllib.parse

import aiohttp
import arrow
import certifi
import opsdroid.events
from emoji import demojize
from opsdroid.connector import Connector, register_event
from opsdroid.connector.slack.create_events import SlackEventCreator
from opsdroid.connector.slack.events import (
    Blocks,
    EditedBlocks,
    ModalOpen,
    ModalPush,
    ModalUpdate,
)
from slack_sdk.errors import SlackApiError
from slack_sdk.socket_mode.aiohttp import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.web.async_client import AsyncWebClient
from voluptuous import Required

_LOGGER = logging.getLogger(__name__)

_USE_BOT_TOKEN_MSG = (
    "Please upgrade your config with a new Slack 'bot-token' instead of the classic 'token'. "
    "Startig v0.22.0 RTM support has been dropped in favour of Socket Mode. "
    "Please check Slack Connector docs for instructions on how to migrate. "
    "https://docs.opsdroid.dev/en/stable/connectors/slack.html"
)
CONFIG_SCHEMA = {
    Required("bot-token", msg=_USE_BOT_TOKEN_MSG): str,
    "socket-mode": bool,
    "app-token": str,
    "bot-name": str,
    "default-room": str,
    "icon-emoji": str,
    "start-thread": bool,
    "refresh-interval": int,
    "channel-limit": int,
}


class ConnectorSlack(Connector):
    """A connector for Slack."""

    def __init__(self, config, opsdroid=None):
        """Create the connector."""
        super().__init__(config, opsdroid=opsdroid)
        _LOGGER.debug(_("Starting Slack connector."))
        self.name = config.get("name", "slack")
        self.bot_token = config["bot-token"]
        self.bot_name = config.get("bot-name", "opsdroid")
        self.default_target = config.get("default-room", "#general")
        self.icon_emoji = config.get("icon-emoji", ":robot_face:")
        self.start_thread = config.get("start-thread", False)
        self.socket_mode = config.get("socket-mode", True)
        self.app_token = config.get("app-token")
        self.channel_limit = config.get("channel-limit", 100)
        self.refresh_interval = config.get("refresh-interval", 600)
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.slack_web_client = AsyncWebClient(
            token=self.bot_token,
            ssl=self.ssl_context,
            proxy=os.environ.get("HTTPS_PROXY"),
        )
        self.socket_mode_client = (
            SocketModeClient(self.app_token, web_client=self.slack_web_client)
            if self.app_token
            else None
        )
        self.auth_info = None
        self.user_info = None
        self.bot_id = None
        self.known_users = {}
        self.known_bots = {}
        self.known_channels = {}

        self._event_creator = SlackEventCreator(self)
        self._event_queue = asyncio.Queue()
        self._event_queue_task = None

    # Add debug to the _queue_worker method
    @debug_timing
    async def _queue_worker(self):
        """Process the event queue with timing information."""
        while True:
            queue_size = self._event_queue.qsize()
            if queue_size > 5:
                _LOGGER.warning(f"DEBUG: Event queue size is large: {queue_size} items")
                
            payload = await self._event_queue.get()
            
            # Determine if this is from a multi-workspace channel
            is_multi_workspace = False
            channel_id = None
            
            if payload.get("type") == "event_callback" and payload.get("event", {}).get("type") == "message":
                channel_id = payload.get("event", {}).get("channel")
                channel_type = await self.get_channel_type(channel_id)
                is_multi_workspace = (channel_type == "multi_workspace")
                
                if is_multi_workspace:
                    _LOGGER.debug(f"DEBUG: Processing queue item from Multi-Workspace channel: {channel_id}")
            
            start_processing = py_time.time()
            try:
                await self.event_handler(payload)
            except Exception as e:
                _LOGGER.error(f"Error processing event: {e}")
            finally:
                processing_time = py_time.time() - start_processing
                self._event_queue.task_done()
                
                # Log slow processing
                if processing_time > 2.0:
                    _LOGGER.warning(
                        f"SLOW PROCESSING: Event took {processing_time:.4f}s to process" + 
                        (f" (Multi-Workspace: {channel_id})" if is_multi_workspace else "")
                    )

    async def connect(self):
        """Connect to the chat service."""
        _LOGGER.info(_("Connecting to Slack."))

        try:
            self.auth_info = (await self.slack_web_client.api_call("auth.test")).data
            self.user_info = (
                await self.slack_web_client.api_call(
                    "users.info",
                    http_verb="GET",
                    params={"user": self.auth_info["user_id"]},
                )
            ).data
            self.bot_id = self.user_info["user"]["profile"]["bot_id"]
            self.opsdroid.create_task(self._get_channels())
        except SlackApiError as error:
            _LOGGER.error(
                _(
                    "Unable to connect to Slack due to %s."
                    "The Slack Connector will not be available."
                ),
                error,
            )
        else:

            if self.socket_mode:
                if not self.socket_mode_client:
                    _LOGGER.error(_(_USE_BOT_TOKEN_MSG))
                    _LOGGER.error(_("The Slack Connector will not be available."))

                    return
                self.socket_mode_client.socket_mode_request_listeners.append(
                    self.socket_event_handler
                )
                await self.socket_mode_client.connect()
                _LOGGER.info(_("Connected successfully with socket mode"))
            else:
                # Create a task for background processing events received by
                # the web event handler.
                self._event_queue_task = asyncio.create_task(self._queue_worker())

                self.opsdroid.web_server.web_app.router.add_post(
                    f"/connector/{self.name}",
                    self.web_event_handler,
                )
                _LOGGER.info(_("Connected successfully with events api"))

            _LOGGER.debug(_("Connected as %s."), self.bot_name)
            _LOGGER.debug(_("Using icon %s."), self.icon_emoji)
            _LOGGER.debug(_("Default room is %s."), self.default_target)

    async def disconnect(self):
        """Disconnect from Slack.

        Cancels the event queue worker task and disconnects the
        socket_mode_client if socket mode was enabled."""

        if self._event_queue_task:
            self._event_queue_task.cancel()
            await asyncio.gather(self._event_queue_task, return_exceptions=True)

        if self.socket_mode_client:
            await self.socket_mode_client.disconnect()
            await self.socket_mode_client.close()

    async def listen(self):
        """Listen for and parse new messages."""

    def _generate_base_data(self, event: opsdroid.events.Event) -> dict:
        """Generate a base data dict to send to the slack API.

        The data dictionary will always contain `channel`, `username`
        and `icon_emoj` which can be derived from the event or the
        slack config.

        If we want to send messages in a thread, we need to include
        thread_ts from the linked event (the message received by opsdroid) and the slack api will know that this new message
        should be included in a thread and not in the channel.

        """
        data = {
            "channel": event.target,
            "username": self.bot_name,
            "icon_emoji": self.icon_emoji,
        }

        if event.linked_event:
            raw_event = event.linked_event.raw_event

            if isinstance(raw_event, dict) and "thread_ts" in raw_event:
                if event.linked_event.event_id != raw_event["thread_ts"]:
                    # Linked Event is inside a thread
                    data["thread_ts"] = raw_event["thread_ts"]
            elif self.start_thread:
                data["thread_ts"] = event.linked_event.event_id

        return data
    
    
    # Add a debug decorator to track execution time of async functions
    def debug_timing(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = py_time.time()
            function_name = func.__name__
            _LOGGER.debug(f"DEBUG: Starting {function_name}")
            
            result = await func(*args, **kwargs)
            
            end_time = py_time.time()
            execution_time = end_time - start_time
            _LOGGER.debug(f"DEBUG: {function_name} took {execution_time:.4f} seconds to execute")
            
            # Log extra info if it took longer than 1 second
            if execution_time > 1.0:
                _LOGGER.warning(f"SLOW OPERATION: {function_name} took {execution_time:.4f} seconds")
                
            return result
        return wrapper

    # Add a channel_type method to identify channel types
    async def get_channel_type(self, channel_id):
        """Identify if a channel is a shared/multi-workspace channel"""
        for channel in self.known_channels.values():
            if channel.get("id") == channel_id:
                if channel.get("is_ext_shared", False) or channel.get("is_shared", False):
                    return "multi_workspace"
                elif channel.get("is_im", False):
                    return "direct_message"
                elif channel.get("is_private", False):
                    return "private_channel"
                else:
                    return "public_channel"
        
        # If not found in cache, try to get it from API
        try:
            _LOGGER.debug(f"DEBUG: Channel {channel_id} not in cache, fetching from API")
            channel_info = await self.slack_web_client.conversations_info(channel=channel_id)
            channel = channel_info.get("channel", {})
            
            # Update cache with this information
            if "name" in channel:
                self.known_channels[channel["name"]] = channel
                
            if channel.get("is_ext_shared", False) or channel.get("is_shared", False):
                return "multi_workspace"
            elif channel.get("is_im", False):
                return "direct_message"
            elif channel.get("is_private", False):
                return "private_channel"
            else:
                return "public_channel"
        except Exception as e:
            _LOGGER.error(f"Error determining channel type: {e}")
            return "unknown"

    # Add the method to ConnectorSlack class
    ConnectorSlack.get_channel_type = get_channel_type

    # Modified _get_channels method with debugging
    @debug_timing
    async def _get_channels(self):
        """Grab all the channels from the Slack API. This method runs while opsdroid
        is running at every refresh_interval.
        """
        max_retries = 5
        while self.opsdroid.eventloop.is_running():
            _LOGGER.info(_("Updating Channels from Slack API at %s."), py_time.asctime())
            cursor = None
            
            # Stats for debugging
            channel_stats = {
                "public_channels": 0,
                "private_channels": 0,
                "multi_workspace": 0,
                "direct_messages": 0
            }

            while max_retries:
                try:
                    _LOGGER.debug("DEBUG: Fetching channels from Slack API")
                    start_time = py_time.time()
                    
                    # Include all channel types including shared channels
                    channels = await self.slack_web_client.conversations_list(
                        cursor=cursor, 
                        limit=self.channel_limit,
                        types="public_channel,private_channel,mpim,im"
                    )
                    
                    api_time = py_time.time() - start_time
                    _LOGGER.debug(f"DEBUG: Slack API call took {api_time:.4f} seconds")
                    
                    # Update the channels cache and collect stats
                    for c in channels["channels"]:
                        # Add flags for different channel types
                        is_shared = c.get("is_ext_shared", False) or c.get("is_shared", False)
                        c["is_multi_workspace"] = is_shared
                        
                        # Update stats
                        if is_shared:
                            channel_stats["multi_workspace"] += 1
                        elif c.get("is_im", False):
                            channel_stats["direct_messages"] += 1
                        elif c.get("is_private", False):
                            channel_stats["private_channels"] += 1
                        else:
                            channel_stats["public_channels"] += 1
                        
                        self.known_channels[c["name"]] = c
                    
                    cursor = channels.get("response_metadata", {}).get("next_cursor")
                    if not cursor:
                        break
                        
                    channel_count = len(self.known_channels.keys())
                    _LOGGER.info(
                        "Grabbed a total of %s channels from Slack", channel_count
                    )
                    
                    # Log channel stats
                    _LOGGER.debug(f"Channel statistics: {channel_stats}")
                    
                    await asyncio.sleep(
                        self.refresh_interval - arrow.now().time().second
                    )
                except SlackApiError as error:
                    if "ratelimited" in str(error):
                        wait_time = float(error.response.headers.get("Retry-After", 30))
                        _LOGGER.warning(
                            _(
                                f"Rate limit threshold reached. Retrying after {wait_time} seconds."
                            )
                        )
                        await asyncio.sleep(wait_time)
                        max_retries -= 1
                        continue
                    else:
                        _LOGGER.error(f"SlackApiError: {error}")
                        raise
            break

# Replace the original method with our debug version
    ConnectorSlack._get_channels = _get_channels

# Add debug to the event handler
    @debug_timing
    async def event_handler(self, payload):
        """Handle different payload types and parse the resulting events with debug timing"""
        
        # Add timing for different parts of event handling
        event_type = payload.get("type", "unknown")
        _LOGGER.debug(f"DEBUG: Processing event of type: {event_type}")
        
        # For message events, check the channel type
        if event_type == "event_callback" and payload.get("event", {}).get("type") == "message":
            event_data = payload.get("event", {})
            channel_id = event_data.get("channel")
            
            # Get channel type and log it
            channel_type_start = py_time.time()
            channel_type = await self.get_channel_type(channel_id)
            channel_type_time = py_time.time() - channel_type_start
            
            _LOGGER.debug(f"DEBUG: Message from channel type: {channel_type} (lookup took {channel_type_time:.4f}s)")
            
            # If multi-workspace, log additional info
            if channel_type == "multi_workspace":
                _LOGGER.debug(f"DEBUG: Processing Multi-Workspace channel message: {channel_id}")

        # Original event handling code
        if "command" in payload:
            payload["type"] = "command"

        event = None
        if "type" in payload:
            create_event_start = py_time.time()
            
            if payload["type"] == "event_callback":
                event = await self._event_creator.create_event(payload["event"], None)
            else:
                event = await self._event_creator.create_event(payload, None)
                
            create_event_time = py_time.time() - create_event_start
            _LOGGER.debug(f"DEBUG: Event creation took {create_event_time:.4f}s")

        if event:
            parse_start = py_time.time()
            
            if isinstance(event, list):
                for e in event:
                    _LOGGER.debug(f"DEBUG: Parsing event: {type(e).__name__}")
                    await self.opsdroid.parse(e)

            if isinstance(event, opsdroid.events.Event):
                _LOGGER.debug(f"DEBUG: Parsing event: {type(event).__name__}")
                await self.opsdroid.parse(event)
                
            parse_time = py_time.time() - parse_start
            _LOGGER.debug(f"DEBUG: Event parsing took {parse_time:.4f}s")
        else:
            _LOGGER.debug(
                "Event returned empty for payload: %s. Event was not parsed", payload
            )

    # Replace the original method with our debug version
        ConnectorSlack.event_handler = event_handler

    async def socket_event_handler(
        self, client: SocketModeClient, req: SocketModeRequest
    ):
        payload = {}

        response = SocketModeResponse(envelope_id=req.envelope_id)
        await client.send_socket_mode_response(response)
        payload = req.payload

        await self.event_handler(payload)

    async def web_event_handler(self, request):
        """Handle events from the Events API and Interactive actions in Slack.
        Following types are handled:
            url_verification, event_callback, block_actions, message_action, view_submission, view_closed

        Return:
            A 200 OK response. The Messenger Platform will resend the webhook
            event every 20 seconds, until a 200 OK response is received.
            Failing to return a 200 OK may cause your webhook to be
            unsubscribed by the Messenger Platform.
        """
        payload = {}

        if request.content_type == "application/x-www-form-urlencoded":
            req = await request.post()

            if "payload" in req:
                payload = json.loads(req["payload"])
            else:
                # Some payloads (ie: view_submission) don't come with proper formatting
                # Convert the request to text, and later attempt to load the json

                if len(req.keys()) == 1:
                    req = await request.text()
                    req = urllib.parse.unquote(req)

                    if "payload={" in req:
                        req = req.replace("payload=", "")
                        payload = json.loads(req)
                else:
                    payload = dict(req)

        elif request.content_type == "application/json":
            payload = await request.json()

        if payload.get("type") == "url_verification":
            return aiohttp.web.json_response({"challenge": payload["challenge"]})

        # Put the event in the queue to process it in the background and
        # immediately acknowledge the reception by returning status code 200.
        # Slack will resend events that have not been acknowledged within 3
        # seconds and we want to avoid that.
        #
        # https://api.slack.com/apis/connections/events-api#the-events-api__responding-to-events
        self._event_queue.put_nowait(payload)

        return aiohttp.web.Response(text=json.dumps("Received"), status=200)

    async def find_channel(self, channel_name):
        """
        Given a channel name return the channel properties.

        args:
            channel_name: the name of the channel. ie: general

        returns:
            dict with channel details

        **Basic Usage Example in a Skill:**

        .. code-block:: python

            from opsdroid.skill import Skill
            from opsdroid.matchers import match_regex

            class SearchMessagesSkill(Skill):
                @match_regex(r"find channel")
                async def find_channel(self, message):
                    """ """
                    slack = self.opsdroid.get_connector("slack")
                    channel = await slack.find_channel(channel_name="general")
                    await message.respond(str(channel))
        """

        if channel_name in self.known_channels:
            return self.known_channels[channel_name]
        _LOGGER.info(_("Channel with name %s not found"), channel_name)

    async def search_history_messages(self, channel, start_time, end_time, limit=100):
        """
        Search for messages in a conversation given the intial and end timestamp.

        args:
            channel: channel id
            start_time: epoch timestamp with micro seconds when to start the search
            end_time: epoch timestime with micro seconds when to end the search
            limit: limit of results per query to the API

        returns:
            list of messages between the that timeframe

        **Basic Usage Example in a Skill:**

        .. code-block:: python

            from opsdroid.skill import Skill
            from opsdroid.matchers import match_regex

            class SearchMessagesSkill(Skill):
                @match_regex(r"search messages")
                async def search_messages(self, message):
                    """ """
                    slack = self.opsdroid.get_connector("slack")
                    messages = await slack.search_history_messages(
                        "CHANEL_ID", start_time="1512085950.000216", end_time="1512104434.000490"
                    )
                    await message.respond(str(messages))
        """
        messages = []
        history = await self.slack_web_client.conversations_history(
            channel=channel, oldest=start_time, latest=end_time, limit=limit
        )
        cursor = history.get("response_metadata", {}).get("next_cursor")

        if limit > 1000:
            _LOGGER.info(
                "Grabbing message history from Slack API. This might take some time"
            )

        while True:
            messages += history["messages"]

            if cursor:
                history = await self.slack_web_client.conversations_history(
                    channel=channel, oldest=start_time, latest=end_time, cursor=cursor
                )
                cursor = history.get("response_metadata", {}).get("next_cursor")
            else:
                break
        messages_count = len(messages)
        _LOGGER.debug("Grabbed a total of %s messages from Slack", messages_count)

        return messages

    # Add debug to the lookup_username method
    @debug_timing
    async def lookup_username(self, userid, is_bot=False):
        """Lookup a username and cache it with timing."""
        _LOGGER.debug(f"DEBUG: Looking up user: {userid}, is_bot: {is_bot}")
        
        if userid in self.known_users:
            _LOGGER.debug(f"DEBUG: Found user {userid} in cache")
            return self.known_users[userid]
        elif userid in self.known_bots:
            _LOGGER.debug(f"DEBUG: Found bot {userid} in cache")
            return self.known_bots[userid]
        else:
            _LOGGER.debug(f"DEBUG: User/bot {userid} not in cache, fetching from API")
            start_time = py_time.time()
            
            response = (
                await self.slack_web_client.users_info(user=userid)
                if not is_bot
                else await self.slack_web_client.bots_info(bot=userid)
            )
            
            api_time = py_time.time() - start_time
            _LOGGER.debug(f"DEBUG: User lookup API call took {api_time:.4f}s")
            
            if "user" in response.data:
                user_info = response.data["user"]
                if isinstance(user_info, dict):
                    self.known_users[userid] = user_info
                return user_info
            elif "bot" in response.data:
                bot_info = response.data["bot"]
                if isinstance(bot_info, dict):
                    self.known_bots[userid] = bot_info
                return bot_info

    # Replace the original method with our debug version
    ConnectorSlack.lookup_username = lookup_username

    async def replace_usernames(self, message):
        """Replace User ID with username in message text."""
        userids = re.findall(r"\<\@([A-Z0-9]+)(?:\|.+)?\>", message)

        for userid in userids:
            user_info = await self.lookup_username(userid)
            message = message.replace(
                "<@{userid}>".format(userid=userid),
                "@{username}".format(username=user_info["name"]),
            )

        return message

    @register_event(opsdroid.events.Message)
    async def _send_message(self, message):
        """Respond with a message."""
        _LOGGER.debug(
            _("Responding with: '%s' in room  %s."), message.text, message.target
        )

        data = self._generate_base_data(message)
        data["text"] = message.text

        return await self.slack_web_client.api_call(
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
        }

        return await self.slack_web_client.api_call(
            "chat.update",
            data=data,
        )

    @register_event(Blocks)
    async def _send_blocks(self, blocks):
        """Respond with structured blocks."""
        _LOGGER.debug(
            _("Responding with interactive blocks in room %s."), blocks.target
        )
        data = self._generate_base_data(blocks)
        data["blocks"] = blocks.blocks

        return await self.slack_web_client.api_call("chat.postMessage", data=data)

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
        }

        return await self.slack_web_client.api_call(
            "chat.update",
            data=data,
        )

    @register_event(ModalOpen)
    async def _open_modal(self, modal):
        """Respond with opening a Modal.

        https://api.slack.com/methods/views.open
        """
        _LOGGER.debug(_("Opening modal with trigger id: %s."), modal.trigger_id)

        return await self.slack_web_client.api_call(
            "views.open",
            data={"trigger_id": modal.trigger_id, "view": modal.view},
        )

    @register_event(ModalUpdate)
    async def _update_modal(self, modal):
        """Respond an update to a Modal.

        https://api.slack.com/methods/views.update
        """
        _LOGGER.debug(_("Opening modal with trigger id: %s."), modal.external_id)
        data = {"external_id": modal.external_id, "view": modal.view}

        if modal.hash:
            data["hash"] = modal.hash

        return await self.slack_web_client.api_call("views.update", data=data)

    @register_event(ModalPush)
    async def _push_modal(self, modal):
        """Respond by pushing a view onto the stack of a root view.

        https://api.slack.com/methods/views.push
        """
        _LOGGER.debug(_("Pushing modal with trigger id: %s."), modal.trigger_id)

        return await self.slack_web_client.api_call(
            "views.push",
            data={"trigger_id": modal.trigger_id, "view": modal.view},
        )

    @register_event(opsdroid.events.Reaction)
    async def send_reaction(self, reaction):
        """React to a message."""
        emoji = demojize(reaction.emoji).replace(":", "")
        _LOGGER.debug(_("Reacting with: %s."), emoji)
        try:
            return await self.slack_web_client.api_call(
                "reactions.add",
                data={
                    "name": emoji,
                    "channel": reaction.target,
                    "timestamp": reaction.linked_event.event_id,
                },
            )
        except SlackApiError as error:
            if "invalid_name" in str(error):
                _LOGGER.warning(_("Slack does not support the emoji %s."), emoji)
            else:
                raise

    @register_event(opsdroid.events.NewRoom)
    async def _send_room_creation(self, creation_event):
        _LOGGER.debug(_("Creating room %s."), creation_event.name)

        return await self.slack_web_client.api_call(
            "conversations.create", data={"name": creation_event.name}
        )

    @register_event(opsdroid.events.RoomName)
    async def _send_room_name_set(self, name_event):
        _LOGGER.debug(
            _("Renaming room %s to '%s'."), name_event.target, name_event.name
        )

        return await self.slack_web_client.api_call(
            "conversations.rename",
            data={"channel": name_event.target, "name": name_event.name},
        )

    @register_event(opsdroid.events.JoinRoom)
    async def _send_join_room(self, join_event):
        return await self.slack_web_client.api_call(
            "conversations.join", data={"channel": join_event.target}
        )

    @register_event(opsdroid.events.UserInvite)
    async def _send_user_invitation(self, invite_event):
        _LOGGER.debug(
            _("Inviting user %s to room '%s'."), invite_event.user, invite_event.target
        )

        return await self.slack_web_client.api_call(
            "conversations.invite",
            data={"channel": invite_event.target, "users": invite_event.user_id},
        )

    @register_event(opsdroid.events.RoomDescription)
    async def _send_room_description(self, desc_event):
        return await self.slack_web_client.api_call(
            "conversations.setTopic",
            data={"channel": desc_event.target, "topic": desc_event.description},
        )

    @register_event(opsdroid.events.PinMessage)
    async def _send_pin_message(self, pin_event):
        return await self.slack_web_client.api_call(
            "pins.add",
            data={
                "channel": pin_event.target,
                "timestamp": pin_event.linked_event.event_id,
            },
        )

    @register_event(opsdroid.events.UnpinMessage)
    async def _send_unpin_message(self, unpin_event):
        return await self.slack_web_client.api_call(
            "pins.remove",
            data={
                "channel": unpin_event.target,
                "timestamp": unpin_event.linked_event.event_id,
            },
        )

    @register_event(opsdroid.events.File)
    async def _send_file(self, file_event):
        raw_event = file_event.raw_event
        thread_ts = (
            raw_event.get("thread_ts", None)
            if self.config.get("start-thread", False) and isinstance(raw_event, dict)
            else None
        )
        return await self.slack_web_client.files_upload_v2(
            channel=file_event.target,
            content=await file_event.get_file_bytes(),
            filename=file_event.name,
            thread_ts=thread_ts,)
