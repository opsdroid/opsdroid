"""A connector for Microsoft Teams."""

import json
import logging
from urllib.parse import unquote

from aiohttp.web import Request, Response
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    MessageFactory,
)
from botbuilder.core.teams import teams_get_channel_id
from botbuilder.core.turn_context import TurnContext
from botbuilder.schema import Activity, ConversationParameters, ConversationReference
from opsdroid.connector import Connector, register_event
from opsdroid.events import Message

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = {
    "app-id": str,
    "password": str,
    "bot-name": str,
}


class TeamsConnector(Connector):
    """A connector for Microsoft Teams."""

    def __init__(self, config, opsdroid=None):
        """Create the connector."""
        self.name = config.get("name", "teams")
        self.config = config
        self.default_target = None  # Teams has no default room
        self.opsdroid = opsdroid
        self.app_id = self.config.get("app-id", "abc123")
        self.app_password = self.config.get("password", "")
        self.adapter = BotFrameworkAdapter(
            BotFrameworkAdapterSettings(self.app_id, self.app_password)
        )
        self.conversation_references = {}
        self.service_endpoints = {}

    async def connect(self):
        """Connect to the chat service."""
        self.service_endpoints = (
            await self.opsdroid.memory.get("teams_service_endpoints") or {}
        )
        self.opsdroid.web_server.web_app.router.add_post(
            f"/connector/{self.name}", self.teams_message_handler
        )

    async def teams_message_handler(self, req: Request) -> Response:
        """Handle incoming webhooks from Teams."""
        if "application/json" in req.headers["Content-Type"]:
            body = await req.json()
            _LOGGER.debug(json.dumps(body))
        else:
            return Response(status=415)

        activity = Activity().deserialize(body)

        # Cache service endpoint for channel
        teams_channel_id = teams_get_channel_id(activity)
        if teams_channel_id not in self.service_endpoints:
            self.service_endpoints[teams_channel_id] = activity.service_url
            await self.opsdroid.memory.put(
                "teams_service_endpoints", self.service_endpoints
            )

        if activity.type == "message":
            message = Message(
                text=activity.text,
                user=activity.from_property.name,
                target=TurnContext.get_conversation_reference(activity),
                connector=self,
                raw_event=TurnContext(self.adapter, activity),
            )
            await self.opsdroid.parse(message)
        else:
            _LOGGER.info(
                f"Recieved {activity.type} activity which is not currently supported."
            )

        return Response(status=200)

    async def listen(self):
        """Listen for new message.

        Listening is handled by the aiohttp web server

        """

    @staticmethod
    def parse_channel_id(channel_id):
        """Extract channel ID from channel link.

        In teams you can get a link to a channel. This function extracts the channel ID
        from that link.

        """
        prefix = "https://teams.microsoft.com/l/channel/"
        if channel_id.startswith(prefix):
            return unquote(channel_id.replace(prefix, "").split("/")[0])
        else:
            return channel_id

    @register_event(Message)
    async def send(self, message: Message):
        """Send a message."""
        if isinstance(message.target, str):
            teams_channel_id = self.parse_channel_id(message.target)
            try:
                connector_client = await self.adapter.create_connector_client(
                    self.service_endpoints[teams_channel_id]
                )
                await connector_client.conversations.create_conversation(
                    ConversationParameters(
                        is_group=True,
                        channel_data={"channel": {"id": teams_channel_id}},
                        activity=MessageFactory.text(message.text),
                    )
                )
            except KeyError:
                _LOGGER.error(
                    "Unable to send a message until someone has spoken to the bot first."
                )

        elif isinstance(message.target, ConversationReference):
            await self.adapter.continue_conversation(
                message.target,
                lambda turn_context: turn_context.send_activity(message.text),
                self.app_id,
            )

        else:
            _LOGGER.error(f"'{message.target}' is not a valid place to send a message.")

    async def disconnect(self):
        """Disconnect from teams.

        Listening is handled by the aiohttp web server

        """
