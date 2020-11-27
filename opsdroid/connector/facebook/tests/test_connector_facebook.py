import pytest
import asynctest.mock as amock

import asyncio

from opsdroid.connector.facebook import ConnectorFacebook
from opsdroid.events import Message


def test_init(opsdroid):
    connector = ConnectorFacebook({}, opsdroid=opsdroid)
    assert connector.default_target is None
    assert connector.name == "facebook"


def test_property(opsdroid):
    connector = ConnectorFacebook({}, opsdroid=opsdroid)
    assert connector.name == "facebook"


@pytest.mark.asyncio
async def test_connect(opsdroid):
    """Test the connect method adds the handlers."""
    connector = ConnectorFacebook({}, opsdroid=opsdroid)
    opsdroid.web_server = amock.CoroutineMock()
    opsdroid.web_server.web_app = amock.CoroutineMock()
    opsdroid.web_server.web_app.router = amock.CoroutineMock()
    opsdroid.web_server.web_app.router.add_get = amock.CoroutineMock()
    opsdroid.web_server.web_app.router.add_post = amock.CoroutineMock()

    await connector.connect()

    assert opsdroid.web_server.web_app.router.add_get.called
    assert opsdroid.web_server.web_app.router.add_post.called


@pytest.mark.asyncio
async def test_facebook_message_handler(opsdroid):
    """Test the new facebook message handler."""
    import aiohttp

    connector = ConnectorFacebook({}, opsdroid=opsdroid)
    req_ob = {
        "object": "page",
        "entry": [
            {
                "messaging": [
                    {"message": {"text": "Hello"}, "sender": {"id": "1234567890"}}
                ]
            }
        ],
    }
    mock_request = amock.CoroutineMock()
    mock_request.json = amock.CoroutineMock()
    mock_request.json.return_value = req_ob

    connector.opsdroid = opsdroid
    connector.opsdroid.parse = amock.CoroutineMock()

    response = await connector.facebook_message_handler(mock_request)
    assert connector.opsdroid.parse.called
    assert isinstance(response, aiohttp.web.Response)
    assert response.status == 200


@pytest.mark.asyncio
async def test_facebook_message_handler_invalid(opsdroid, caplog):
    """Test the new facebook message handler for invalid message."""
    import aiohttp

    connector = ConnectorFacebook({}, opsdroid=opsdroid)
    req_ob = {
        "object": "page",
        "entry": [{"messaging": [{"message": {"text": "Hello"}, "sender": {}}]}],
    }
    mock_request = amock.CoroutineMock()
    mock_request.json = amock.CoroutineMock()
    mock_request.json.return_value = req_ob

    connector.opsdroid = opsdroid
    connector.opsdroid.parse = amock.CoroutineMock()

    response = await connector.facebook_message_handler(mock_request)
    assert not connector.opsdroid.parse.called
    assert "Unable to process message." in caplog.text
    assert isinstance(response, aiohttp.web.Response)
    assert response.status == 200


@pytest.mark.asyncio
async def test_facebook_challenge_handler(opsdroid):
    """Test the facebook challenge handler."""
    import aiohttp

    connector = ConnectorFacebook({"verify-token": "token_123"}, opsdroid=opsdroid)
    mock_request = amock.Mock()
    mock_request.query = {
        "hub.verify_token": "token_123",
        "hub.challenge": "challenge_123",
    }

    response = await connector.facebook_challenge_handler(mock_request)
    assert isinstance(response, aiohttp.web.Response)
    assert response.text == "challenge_123"
    assert response.status == 200

    mock_request.query = {
        "hub.verify_token": "token_abc",
        "hub.challenge": "challenge_123",
    }
    response = await connector.facebook_challenge_handler(mock_request)
    assert isinstance(response, aiohttp.web.Response)
    assert response.status == 403


@pytest.mark.asyncio
async def test_listen(opsdroid):
    """Test that listen does nothing."""
    connector = ConnectorFacebook({}, opsdroid=opsdroid)
    await connector.listen()
    assert True  # Listen should not block and return immediately


@pytest.mark.asyncio
async def test_respond(opsdroid):
    """Test that responding sends a message."""
    post_response = amock.Mock()
    post_response.status = 200

    with amock.patch(
        "aiohttp.ClientSession.post", new=amock.CoroutineMock()
    ) as patched_request:
        assert opsdroid.__class__.instances
        connector = ConnectorFacebook({}, opsdroid=opsdroid)
        room = "a146f52c-548a-11e8-a7d1-28cfe949e12d"
        test_message = Message(
            text="Hello world", user="Alice", target=room, connector=connector
        )
        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(post_response)
        await test_message.respond("Response")
        assert patched_request.called


@pytest.mark.asyncio
async def test_respond_bad_response(opsdroid):
    """Test that responding sends a message and get bad response."""
    post_response = amock.Mock()
    post_response.status = 401
    post_response.text = amock.CoroutineMock()
    post_response.text.return_value = "Error"

    with amock.patch(
        "aiohttp.ClientSession.post", new=amock.CoroutineMock()
    ) as patched_request:
        assert opsdroid.__class__.instances
        connector = ConnectorFacebook({}, opsdroid=opsdroid)
        room = "a146f52c-548a-11e8-a7d1-28cfe949e12d"
        test_message = Message(
            text="Hello world", user="Alice", target=room, connector=connector
        )
        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(post_response)
        await test_message.respond("Response")
        assert patched_request.called
        assert post_response.text.called
