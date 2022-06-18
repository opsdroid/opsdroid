import asyncio
import unittest
import pytest
import json

import asynctest
import asynctest.mock as amock
from aiohttp.web import HTTPUnauthorized

from opsdroid.cli.start import configure_lang
from opsdroid.connector.websocket import ConnectorWebsocket, WebsocketMessage
from opsdroid.core import OpsDroid
from opsdroid.events import Message


class TestConnectorWebsocket(unittest.TestCase):
    """Test the opsdroid Websocket connector class."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        configure_lang({})

    def test_init(self):
        connector = ConnectorWebsocket({}, opsdroid=OpsDroid())
        self.assertEqual(None, connector.default_target)
        self.assertEqual("websocket", connector.name)

    def test_property(self):
        connector = ConnectorWebsocket({}, opsdroid=OpsDroid())
        self.assertEqual("websocket", connector.name)


class TestConnectorWebsocketAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid Websocket connector class."""

    async def setUp(self):
        configure_lang({})

    async def test_connect(self):
        """Test the connect method adds the handlers."""
        opsdroid = amock.CoroutineMock()
        connector = ConnectorWebsocket({}, opsdroid=opsdroid)
        opsdroid.web_server = amock.CoroutineMock()
        opsdroid.web_server.web_app = amock.CoroutineMock()
        opsdroid.web_server.web_app.router = amock.CoroutineMock()
        opsdroid.web_server.web_app.router.add_get = amock.CoroutineMock()
        opsdroid.web_server.web_app.router.add_post = amock.CoroutineMock()

        await connector.connect()

        self.assertTrue(opsdroid.web_server.web_app.router.add_get.called)
        self.assertTrue(opsdroid.web_server.web_app.router.add_post.called)

    async def test_disconnect(self):
        """Test the disconnect method closes all sockets."""
        connector = ConnectorWebsocket({}, opsdroid=OpsDroid())

        connector.active_connections = {
            "connection1": amock.CoroutineMock(),
            "connection2": amock.CoroutineMock(),
        }

        connector.active_connections["connection1"].close = amock.CoroutineMock()
        connector.active_connections["connection2"].close = amock.CoroutineMock()

        await connector.disconnect()

        self.assertTrue(connector.active_connections["connection1"].close.called)
        self.assertTrue(connector.active_connections["connection2"].close.called)
        self.assertFalse(connector.accepting_connections)

    async def test_new_websocket_handler(self):
        """Test the new websocket handler."""
        import aiohttp.web

        connector = ConnectorWebsocket({}, opsdroid=OpsDroid())
        connector.max_connections = 1
        self.assertEqual(len(connector.available_connections), 0)

        mocked_request = amock.Mock()

        response = await connector.new_websocket_handler(mocked_request)
        self.assertTrue(isinstance(response, aiohttp.web.Response))
        self.assertEqual(len(connector.available_connections), 1)
        self.assertEqual(response.status, 200)

        fail_response = await connector.new_websocket_handler(mocked_request)
        self.assertTrue(isinstance(fail_response, aiohttp.web.Response))
        self.assertEqual(fail_response.status, 429)

    async def test_lookup_username(self):
        """Test lookup up the username."""
        connector = ConnectorWebsocket({}, opsdroid=OpsDroid())
        self.assertEqual("websocket", connector.name)

    async def test_listen(self):
        """Test that listen does nothing."""
        connector = ConnectorWebsocket({}, opsdroid=OpsDroid())
        await connector.listen()

    async def test_respond(self):
        """Test that responding sends a message down the correct websocket."""
        with OpsDroid() as opsdroid:
            self.assertTrue(opsdroid.__class__.instances)
            connector = ConnectorWebsocket({}, opsdroid=opsdroid)
            room = "a146f52c-548a-11e8-a7d1-28cfe949e12d"
            connector.active_connections[room] = amock.CoroutineMock()
            connector.active_connections[room].send_str = amock.CoroutineMock()
            test_message = Message(
                text="Hello world", user="Alice", target=room, connector=connector
            )
            await test_message.respond("Response")
            self.assertTrue(connector.active_connections[room].send_str.called)

            connector.active_connections[room].send_str.reset_mock()
            test_message.target = None
            await test_message.respond("Response")
            self.assertTrue(connector.active_connections[room].send_str.called)

            connector.active_connections[room].send_str.reset_mock()
            test_message.target = "Invalid Room"
            await test_message.respond("Response")
            self.assertFalse(connector.active_connections[room].send_str.called)

    async def test_websocket_handler(self):
        """Test the websocket handler."""
        from datetime import datetime, timedelta

        import aiohttp

        connector = ConnectorWebsocket({}, opsdroid=OpsDroid())
        room = "a146f52c-548a-11e8-a7d1-28cfe949e12d"
        mock_request = amock.Mock()
        mock_request.match_info = amock.Mock()
        mock_request.match_info.get = amock.Mock()
        mock_request.match_info.get.return_value = room
        connector.available_connections = [{"id": room, "date": datetime.now()}]

        with OpsDroid() as opsdroid, amock.patch(
            "aiohttp.web.WebSocketResponse", new=asynctest.MagicMock()
        ) as mock_WebSocketResponse:
            connector.opsdroid = opsdroid
            connector.opsdroid.parse = amock.CoroutineMock()
            mock_socket = asynctest.MagicMock()
            mock_socket.prepare = amock.CoroutineMock()
            mock_socket.exception = amock.CoroutineMock()
            socket_message_1 = amock.CoroutineMock()
            socket_message_1.type = aiohttp.WSMsgType.TEXT
            socket_message_1.data = "Hello world!"
            socket_message_2 = amock.CoroutineMock()
            socket_message_2.type = aiohttp.WSMsgType.ERROR
            socket_message_2.data = "Error!"
            mock_socket.__aiter__.return_value = [socket_message_1, socket_message_2]
            mock_WebSocketResponse.return_value = mock_socket
            response = await connector.websocket_handler(mock_request)
            self.assertEqual(response, mock_socket)
            self.assertTrue(mock_socket.prepare)
            self.assertTrue(connector.opsdroid.parse.called)
            self.assertTrue(mock_socket.exception.called)
            self.assertFalse(connector.available_connections)
            self.assertFalse(connector.active_connections)

            response = await connector.websocket_handler(mock_request)
            self.assertEqual(type(response), aiohttp.web.Response)
            self.assertEqual(response.status, 400)

            connector.available_connections = [
                {"id": room, "date": datetime.now() - timedelta(seconds=120)}
            ]
            response = await connector.websocket_handler(mock_request)
            self.assertEqual(type(response), aiohttp.web.Response)
            self.assertEqual(response.status, 408)
            self.assertFalse(connector.available_connections)


def test_ConnectorMessage_dataclass():
    payload = json.dumps({"message": "Hello, world!", "user": "Bob", "socket": "12345"})
    data = WebsocketMessage.parse_payload(payload)

    assert data.message == "Hello, world!"
    assert data.user == "Bob"
    assert data.socket == "12345"

    text_message = WebsocketMessage.parse_payload("Hello, world!")
    assert text_message.message == "Hello, world!"
    assert text_message.user is None
    assert text_message.socket is None


@pytest.mark.asyncio
async def test_validate_request():
    config = {"token": "secret"}
    connector = ConnectorWebsocket(config, opsdroid=OpsDroid())

    request = amock.CoroutineMock()
    request.headers = {"Authorization": "secret"}

    is_valid = await connector.validate_request(request)
    assert is_valid

    request = amock.CoroutineMock()
    request.headers = {}

    with pytest.raises(HTTPUnauthorized):
        await connector.validate_request(request)


@pytest.mark.asyncio
async def test_new_websocket_handler_no_token():
    config = {"token": "secret"}
    connector = ConnectorWebsocket(config, opsdroid=OpsDroid())

    with pytest.raises(HTTPUnauthorized):
        request = amock.CoroutineMock()
        request.headers = {}
        await connector.new_websocket_handler(request)
