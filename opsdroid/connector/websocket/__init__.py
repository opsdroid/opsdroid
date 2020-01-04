"""A connector which allows websocket connections."""
import logging
import json
import uuid
from datetime import datetime

import aiohttp
import aiohttp.web
from aiohttp import WSCloseCode

from opsdroid.connector import Connector, register_event
from opsdroid.events import Message


_LOGGER = logging.getLogger(__name__)
HEADERS = {"Access-Control-Allow-Origin": "*"}
CONFIG_SCHEMA = {"bot-name": str, "max-connections": int, "connection-timeout": int}


class ConnectorWebsocket(Connector):
    """A connector which allows websocket connections."""

    def __init__(self, config, opsdroid=None):
        """Create the connector."""
        super().__init__(config, opsdroid=opsdroid)
        _LOGGER.debug(_("Starting Websocket connector."))
        self.name = "websocket"
        self.max_connections = self.config.get("max-connections", 10)
        self.connection_timeout = self.config.get("connection-timeout", 60)
        self.accepting_connections = True
        self.active_connections = {}
        self.available_connections = []
        self.bot_name = self.config.get("bot-name", "opsdroid")

    async def connect(self):
        """Connect to the chat service."""
        self.accepting_connections = True

        self.opsdroid.web_server.web_app.router.add_get(
            "/connector/websocket/{socket}", self.websocket_handler
        )

        self.opsdroid.web_server.web_app.router.add_post(
            "/connector/websocket", self.new_websocket_handler
        )

    async def disconnect(self):
        """Disconnect from current sessions."""
        self.accepting_connections = False
        connections_to_close = self.active_connections.copy()
        for connection in connections_to_close:
            await connections_to_close[connection].close(
                code=WSCloseCode.GOING_AWAY, message="Server shutdown"
            )

    async def new_websocket_handler(self, request):
        """Handle for aiohttp creating websocket connections."""
        if (
            len(self.active_connections) + len(self.available_connections)
            < self.max_connections
            and self.accepting_connections
        ):
            socket = {"id": str(uuid.uuid1()), "date": datetime.now()}
            self.available_connections.append(socket)
            return aiohttp.web.Response(
                text=json.dumps({"socket": socket["id"]}), headers=HEADERS, status=200
            )
        return aiohttp.web.Response(
            text=json.dumps("No connections available"), headers=HEADERS, status=429
        )

    async def websocket_handler(self, request):
        """Handle for aiohttp handling websocket connections."""
        socket = request.match_info.get("socket")
        available = [
            item for item in self.available_connections if item["id"] == socket
        ]
        if len(available) != 1:
            return aiohttp.web.Response(
                text=json.dumps("Please request a socket first"),
                headers=HEADERS,
                status=400,
            )
        if (
            datetime.now() - available[0]["date"]
        ).total_seconds() > self.connection_timeout:
            self.available_connections.remove(available[0])
            return aiohttp.web.Response(
                text=json.dumps("Socket request timed out"), headers=HEADERS, status=408
            )
        self.available_connections.remove(available[0])
        _LOGGER.debug(_("User connected to %s."), socket)

        websocket = aiohttp.web.WebSocketResponse()
        await websocket.prepare(request)

        self.active_connections[socket] = websocket
        async for msg in websocket:
            if msg.type == aiohttp.WSMsgType.TEXT:
                message = Message(text=msg.data, user=None, target=None, connector=self)
                await self.opsdroid.parse(message)
            elif msg.type == aiohttp.WSMsgType.ERROR:
                _LOGGER.error(
                    _("Websocket connection closed with exception %s."),
                    websocket.exception(),
                )

        _LOGGER.info(_("websocket connection closed"))
        self.active_connections.pop(socket, None)

        return websocket

    async def listen(self):
        """Listen for and parse new messages.

        Listening is handled by the aiohttp web server so
        we don't need to do anything here.

        """

    @register_event(Message)
    async def send_message(self, message):
        """Respond with a message."""
        try:
            if message.target is None:
                message.target = next(iter(self.active_connections))
            _LOGGER.debug(
                _("Responding with: '%s' in target %s"), message.text, message.target
            )
            await self.active_connections[message.target].send_str(message.text)
        except KeyError:
            _LOGGER.error(_("No active socket for target %s"), message.target)
