import json
from unittest.mock import AsyncMock,MagicMock, Mock, patch

import anyio
import pytest
from aiohttp.web_exceptions import HTTPUnauthorized

from opsdroid.cli.utils import configure_lang
from opsdroid.connector.websocket import ConnectorWebsocket, WebsocketMessage
from opsdroid.core import OpsDroid
from opsdroid.events import Message

@pytest.mark.anyio
async def test_init():
    connector = ConnectorWebsocket({}, opsdroid=OpsDroid())
    assert connector.default_target is None
    assert connector.name == 'websocket'


@pytest.mark.anyio
async def test_property():
    connector = ConnectorWebsocket({}, opsdroid=OpsDroid())
    assert connector.name == 'websocket'


@pytest.mark.anyio
async def test_connect():
    """Test the connect method adds the handlers."""
    opsdroid = AsyncMock(test_property)
    connector = ConnectorWebsocket({}, opsdroid=opsdroid)
    opsdroid.web_server = AsyncMock()
    opsdroid.web_server.web_app = AsyncMock()
    opsdroid.web_server.web_app.router = AsyncMock()
    opsdroid.web_server.web_app.router.add_get = AsyncMock()
    opsdroid.web_server.web_app.router.add_post = AsyncMock()

    await connector.connect()

    assert opsdroid.web_server.web_app.router.add_get.called
    assert opsdroid.web_server.web_app.router.add_post.called


@pytest.mark.anyio
async def test_disconnect():
    """Test the disconnect method closes all sockets."""
    connector = ConnectorWebsocket({}, opsdroid=OpsDroid())

    connector.active_connections = {
        "connection1": AsyncMock(),
        "connection2": AsyncMock(),
    }

    connector.active_connections["connection1"].close = AsyncMock()
    connector.active_connections["connection2"].close = AsyncMock()

    await connector.disconnect()

    assert connector.active_connections['connection1'].close.called
    assert connector.active_connections['connection2'].close.called
    assert not connector.accepting_connections


@pytest.mark.anyio
async def test_new_websocket_handler():
    """Test the new websocket handler."""
    import aiohttp.web

    connector = ConnectorWebsocket({}, opsdroid=OpsDroid())
    connector.max_connections = 1
    assert len(connector.available_connections) == 0

    mocked_request = Mock()

    response = await connector.new_websocket_handler(mocked_request)
    assert isinstance(response, aiohttp.web.Response)
    assert len(connector.available_connections) == 1
    assert response.status == 200

    fail_response = await connector.new_websocket_handler(mocked_request)
    assert isinstance(fail_response, aiohttp.web.Response)
    assert fail_response.status == 429


@pytest.mark.anyio
async def test_lookup_username():
    """Test lookup up the username."""
    connector = ConnectorWebsocket({}, opsdroid=OpsDroid())
    assert connector.name == 'websocket'

@pytest.mark.anyio
async def test_listen():
    """Test that listen does nothing."""
    connector = ConnectorWebsocket({}, opsdroid=OpsDroid())
    await connector.listen()


@pytest.mark.anyio
async def test_respond(opsdroid):
    """Test that responding sends a message down the correct websocket."""
    connector = ConnectorWebsocket({}, opsdroid=opsdroid)
    room = "a146f52c-548a-11e8-a7d1-28cfe949e12d"
    connector.active_connections[room] = AsyncMock()
    connector.active_connections[room].send_str = AsyncMock()
    test_message = Message(
        text="Hello world", user="Alice", target=room, connector=connector
    )
    await test_message.respond("Response")
    assert connector.active_connections[room].send_str.called

    connector.active_connections[room].send_str.reset_mock()
    test_message.target = None
    await test_message.respond("Response")
    assert connector.active_connections[room].send_str.called

    connector.active_connections[room].send_str.reset_mock()
    test_message.target = "Invalid Room"
    await test_message.respond("Response")
    assert not connector.active_connections[room].send_str.called


@pytest.mark.anyio
async def test_websocket_handler():
    """Test the websocket handler."""
    from datetime import datetime, timedelta

    import aiohttp

    connector = ConnectorWebsocket({}, opsdroid=OpsDroid())
    room = "a146f52c-548a-11e8-a7d1-28cfe949e12d"
    mock_request = Mock()
    mock_request.match_info = Mock()
    mock_request.match_info.get = Mock()
    mock_request.match_info.get.return_value = room
    connector.available_connections = [{"id": room, "date": datetime.now()}]

    with OpsDroid() as opsdroid, patch(
        "aiohttp.web.WebSocketResponse", new=MagicMock()
    ) as mock_WebSocketResponse:
        connector.opsdroid = opsdroid
        connector.opsdroid.parse = AsyncMock()
        mock_socket = MagicMock()
        mock_socket.prepare = AsyncMock()
        mock_socket.exception = AsyncMock()
        socket_message_1 = AsyncMock()
        socket_message_1.type = aiohttp.WSMsgType.TEXT
        socket_message_1.data = "Hello world!"
        socket_message_2 = AsyncMock()
        socket_message_2.type = aiohttp.WSMsgType.ERROR
        socket_message_2.data = "Error!"
        mock_socket.__aiter__.return_value = [socket_message_1, socket_message_2]
        mock_WebSocketResponse.return_value = mock_socket
        response = await connector.websocket_handler(mock_request)
        assert response == mock_socket
        assert mock_socket.prepare
        assert connector.opsdroid.parse.called
        assert mock_socket.exception.called
        assert not connector.available_connections
        assert not connector.active_connections

        response = await connector.websocket_handler(mock_request)
        assert type(response) == aiohttp.web.Response
        assert response.status == 400

        connector.available_connections = [
            {"id": room, "date": datetime.now() - timedelta(seconds=120)}
        ]
        response = await connector.websocket_handler(mock_request)
        assert type(response) == aiohttp.web.Response
        assert response.status == 408
        assert not connector.available_connections


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


@pytest.mark.anyio
async def test_validate_request():
    config = {"token": "secret"}
    connector = ConnectorWebsocket(config, opsdroid=OpsDroid())

    request = AsyncMock()
    request.headers = {"Authorization": "secret"}
    is_valid = await connector.validate_request(request)
    assert is_valid

    request = AsyncMock()
    request.headers = {}

    with pytest.raises(HTTPUnauthorized):
        await connector.validate_request(request)


@pytest.mark.anyio
async def test_new_websocket_handler_no_token():
    config = {"token": "secret"}
    connector = ConnectorWebsocket(config, opsdroid=OpsDroid())

    with pytest.raises(HTTPUnauthorized):
        request = AsyncMock()
        request.headers = {}
        await connector.new_websocket_handler(request)




