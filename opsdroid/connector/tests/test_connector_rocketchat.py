"""Tests for the RocketChat connector."""
import asyncio
import pytest
import contextlib
import asynctest.mock as amock

from opsdroid.connector.rocketchat import RocketChat
from opsdroid.events import Message
from opsdroid.cli.start import configure_lang

configure_lang({})


def test_init(opsdroid):
    """Test that the connector is initialised properly."""
    connector = RocketChat(
        {
            "name": "rocket.chat",
            "token": "test",
            "user-id": "userID",
            "update-interval": 0.1,
        },
        opsdroid=opsdroid,
    )
    assert connector.default_target == "general"
    assert connector.name == "rocket.chat"


def test_missing_token(caplog):
    """Test that attempt to connect without info raises an error."""

    RocketChat({})
    assert "Unable to login: Access token is missing." in caplog.text


@pytest.mark.asyncio
async def test_connect(opsdroid, caplog):
    connector = RocketChat(
        {
            "name": "rocket.chat",
            "token": "test",
            "user-id": "userID",
            "default_target": "test",
        },
        opsdroid=opsdroid,
    )
    connect_response = amock.Mock()
    connect_response.status = 200
    connect_response.json = amock.CoroutineMock()
    connect_response.return_value = {
        "_id": "3vABZrQgDzfcz7LZi",
        "name": "Fábio Rosado",
        "emails": [{"address": "fabioglrosado@gmail.com", "verified": True}],
        "status": "online",
        "statusConnection": "online",
        "username": "FabioRosado",
        "utcOffset": 1,
        "active": True,
        "roles": ["user"],
        "settings": {},
        "email": "fabioglrosado@gmail.com",
        "success": True,
    }

    with amock.patch("aiohttp.ClientSession.get") as patched_request:

        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(connect_response)

        await connector.connect()
        assert patched_request.status != 200
        assert patched_request.called
        assert "Connected" in caplog.text


@pytest.mark.asyncio
async def test_connect_failure(opsdroid, caplog):
    connector = RocketChat(
        {
            "name": "rocket.chat",
            "token": "test",
            "user-id": "userID",
            "default_target": "test",
        },
        opsdroid=opsdroid,
    )
    result = amock.MagicMock()
    result.status = 401

    with amock.patch("aiohttp.ClientSession.get") as patched_request:

        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(result)

        await connector.connect()
        assert "Rocket.Chat error" in caplog.text


@pytest.mark.asyncio
async def test_get_message(opsdroid, caplog):
    connector = RocketChat(
        {
            "name": "rocket.chat",
            "token": "test",
            "user-id": "userID",
            "default_target": "test",
        },
        opsdroid=opsdroid,
    )
    connector.group = "test"
    response = amock.Mock()
    response.status = 200
    response.json = amock.CoroutineMock()
    response.return_value = {
        "messages": [
            {
                "_id": "ZbhuIO764jOIu",
                "rid": "Ipej45JSbfjt9",
                "msg": "hows it going",
                "ts": "2018-05-11T16:05:41.047Z",
                "u": {
                    "_id": "ZbhuIO764jOIu",
                    "username": "FabioRosado",
                    "name": "Fábio Rosado",
                },
                "_updatedAt": "2018-05-11T16:05:41.489Z",
                "editedBy": None,
                "editedAt": None,
                "emoji": None,
                "avatar": None,
                "alias": None,
                "customFields": None,
                "attachments": None,
                "mentions": [],
                "channels": [],
            }
        ]
    }

    with amock.patch.object(
        connector.session, "get"
    ) as patched_request, amock.patch.object(
        connector, "_parse_message"
    ) as mocked_parse_message, amock.patch(
        "asyncio.sleep"
    ) as mocked_sleep:

        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(response)

        await connector._get_message()

        assert patched_request.called
        assert mocked_parse_message.called
        assert mocked_sleep.called
        assert "Received message from Rocket.Chat" in caplog.text


@pytest.mark.asyncio
async def test_parse_message(opsdroid, caplog):
    connector = RocketChat(
        {
            "name": "rocket.chat",
            "token": "test",
            "user-id": "userID",
            "default_target": "test",
        },
        opsdroid=opsdroid,
    )
    response = {
        "messages": [
            {
                "_id": "ZbhuIO764jOIu",
                "rid": "Ipej45JSbfjt9",
                "msg": "hows it going",
                "ts": "2018-05-11T16:05:41.047Z",
                "u": {
                    "_id": "ZbhuIO764jOIu",
                    "username": "FabioRosado",
                    "name": "Fábio Rosado",
                },
                "_updatedAt": "2018-05-11T16:05:41.489Z",
                "editedBy": None,
                "editedAt": None,
                "emoji": None,
                "avatar": None,
                "alias": None,
                "customFields": None,
                "attachments": None,
                "mentions": [],
                "channels": [],
            }
        ]
    }

    with amock.patch.object(connector, "get_messages_loop"), amock.patch(
        "opsdroid.core.OpsDroid.parse"
    ) as mocked_parse:
        await connector._parse_message(response)
        assert mocked_parse.called
        assert "2018-05-11T16:05:41.047Z", connector.latest_update
        assert "Received message from Rocket.Chat" in caplog.text


@pytest.mark.asyncio
async def test_listen(opsdroid):
    connector = RocketChat(
        {
            "name": "rocket.chat",
            "token": "test",
            "user-id": "userID",
            "default_target": "test",
        },
        opsdroid=opsdroid,
    )
    with amock.patch.object(
        connector.loop, "create_task"
    ) as mocked_task, amock.patch.object(
        connector._closing, "wait"
    ) as mocked_event, amock.patch.object(
        connector, "get_messages_loop"
    ):
        mocked_event.return_value = asyncio.Future()
        mocked_event.return_value.set_result(True)
        mocked_task.return_value = asyncio.Future()
        await connector.listen()

        assert mocked_event.called
        assert mocked_task.called


@pytest.mark.asyncio
async def test_get_message_failure(opsdroid, caplog):
    connector = RocketChat(
        {
            "name": "rocket.chat",
            "token": "test",
            "user-id": "userID",
            "default_target": "test",
        },
        opsdroid=opsdroid,
    )
    listen_response = amock.Mock()
    listen_response.status = 401

    with amock.patch.object(connector.session, "get") as patched_request:

        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(listen_response)
        await connector._get_message()
        assert "ERROR    " in caplog.text
        assert connector.listening is False


@pytest.mark.asyncio
async def test_get_messages_loop(opsdroid):
    connector = RocketChat(
        {
            "name": "rocket.chat",
            "token": "test",
            "user-id": "userID",
            "default_target": "test",
        },
        opsdroid=opsdroid,
    )
    connector._get_messages = amock.CoroutineMock()
    connector._get_messages.side_effect = Exception()
    with contextlib.suppress(Exception):
        await connector.get_messages_loop()


@pytest.mark.asyncio
async def test_respond(opsdroid, capsys):
    connector = RocketChat(
        {
            "name": "rocket.chat",
            "token": "test",
            "user-id": "userID",
            "default_target": "test",
        },
        opsdroid=opsdroid,
    )
    post_response = amock.Mock()
    post_response.status = 200

    with amock.patch.object(connector.session, "post") as patched_request:

        assert opsdroid.__class__.instances
        test_message = Message(
            text="This is a test", user="opsdroid", target="test", connector=connector,
        )

        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(post_response)
        await test_message.respond("Response")
        assert patched_request.called


@pytest.mark.asyncio
async def test_respond_failure(opsdroid):
    connector = RocketChat(
        {
            "name": "rocket.chat",
            "token": "test",
            "user-id": "userID",
            "default_target": "test",
        },
        opsdroid=opsdroid,
    )
    post_response = amock.Mock()
    post_response.status = 401

    with amock.patch.object(connector.session, "post") as patched_request:

        assert opsdroid.__class__.instances
        test_message = Message(
            text="This is a test", user="opsdroid", target="test", connector=connector,
        )

        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(post_response)
        await test_message.respond("Response")


@pytest.mark.asyncio
async def test_disconnect(opsdroid):
    connector = RocketChat(
        {
            "name": "rocket.chat",
            "token": "test",
            "user-id": "userID",
            "default_target": "test",
        },
        opsdroid=opsdroid,
    )
    with amock.patch.object(connector.session, "close") as mocked_close:
        mocked_close.return_value = asyncio.Future()
        mocked_close.return_value.set_result(True)

        await connector.disconnect()
        assert connector.listening is False
        assert connector.session.closed()
        assert connector._closing.set() is None
