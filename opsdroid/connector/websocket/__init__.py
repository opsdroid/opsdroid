"""A connector which allows websocket connections."""
import logging
import json
import uuid
from datetime import datetime

import aiohttp
import aiohttp.web

from opsdroid.connector import Connector
from opsdroid.message import Message


_LOGGER = logging.getLogger(__name__)


class ConnectorWebsocket(Connector):
    """A connector which allows websocket connections."""

    def __init__(self, config):
        """Create the connector."""
        super().__init__(config)
        _LOGGER.debug("Starting Websocket connector")
        self.name = "websocket"
        self.config = config
        self.opsdroid = None
        self.default_room = None
        self.max_connections = self.config.get("max-connections", 10)
        self.connection_timeout = self.config.get("connection-timeout", 60)
        self.active_connections = {}
        self.available_connections = []
        self.bot_name = self.config.get("bot-name", 'opsdroid')

    async def connect(self, opsdroid):
        """Connect to the chat service."""
        self.opsdroid = opsdroid

        self.opsdroid.web_server.web_app.router.add_get(
            "/connector/websocket/{socket}",
            self.websocket_handler)

        self.opsdroid.web_server.web_app.router.add_post(
            "/connector/websocket",
            self.new_websocket_handler)

    async def new_websocket_handler(self, request):
        """Handle for aiohttp creating websocket connections."""
        if len(self.active_connections) + len(self.available_connections) \
                < self.max_connections:
            socket = {"id": str(uuid.uuid1()), "date": datetime.now()}
            self.available_connections.append(socket)
            return aiohttp.web.Response(
                text=json.dumps({"socket": socket["id"]}), status=200)
        return aiohttp.web.Response(
            text=json.dumps("No connections available"), status=429)

    async def websocket_handler(self, request):
        """Handle for aiohttp handling websocket connections."""
        socket = request.match_info.get('socket')
        available = [item for item in self.available_connections
                     if item["id"] == socket]
        if len(available) != 1:
            return aiohttp.web.Response(
                text=json.dumps("Please request a socket first"), status=400)
        if (datetime.now() - available[0]["date"]).total_seconds() \
                > self.connection_timeout:
            self.available_connections.remove(available[0])
            return aiohttp.web.Response(
                text=json.dumps("Socket request timed out"), status=408)
        self.available_connections.remove(available[0])
        _LOGGER.debug("User connected to %s", socket)

        websocket = aiohttp.web.WebSocketResponse()
        await websocket.prepare(request)

        self.active_connections[socket] = websocket

        async for msg in websocket:
            if msg.type == aiohttp.WSMsgType.TEXT:
                message = Message(msg.data, None, socket, self)
                await self.opsdroid.parse(message)
            elif msg.type == aiohttp.WSMsgType.ERROR:
                _LOGGER.error('Websocket connection closed with exception %s',
                              websocket.exception())

        _LOGGER.info('websocket connection closed')
        self.active_connections.pop(socket, None)

        return websocket

    async def listen(self, opsdroid):
        """Listen for and parse new messages."""
        pass  # Listening is handled by the aiohttp web server

    async def respond(self, message, room=None):
        """Respond with a message."""
        try:
            if message.room is None:
                message.room = next(iter(self.active_connections))
            _LOGGER.debug("Responding with: '" + message.text +
                          "' in room " + message.room)
            await self.active_connections[message.room].send_str(message.text)
        except KeyError:
            _LOGGER.error("No active socket for room %s", message.room)
