"""Tests for the RocketChat class."""

import logging
import pytest
from pathlib import Path


from opsdroid.connector.gitter import ConnectorGitter
from opsdroid.events import Message
from opsdroid.matchers import match_regex
from opsdroid.testing import running_opsdroid


@pytest.fixture
async def connector(opsdroid, mock_api_obj):
    opsdroid.config["connectors"] = {
        "gitter": {
            "token": "abc123",
            "room-id": "foo",
            "api-base-url": mock_api_obj.base_url,
            "api-stream-url": mock_api_obj.base_url,
            "update-interval": 0.01,
        }
    }
    await opsdroid.load()
    return opsdroid.get_connector("gitter")


def get_response_path(response):
    return Path(__file__).parent / "responses" / response


def test_init():
    """Test that the connector is initialised properly."""
    connector = ConnectorGitter(
        {"bot-name": "github", "room-id": "test-id", "token": "test-token"}
    )
    assert connector.default_target is None
    assert connector.name == "gitter"


async def test_build_url(connector):
    assert "test/api/test-id/chatMessages?access_token=token" == connector.build_url(
        "test/api", "test-id", "chatMessages", access_token="token"
    )


@pytest.mark.asyncio
async def test_parse_message(connector):
    message = await connector.parse_message(
        b'{"text":"hello", "fromUser":{"username":"testUSer", "id": "123"}}'
    )
    assert isinstance(message, Message)


@pytest.mark.asyncio
async def test_parse_message_key_error(connector, caplog):
    await connector.parse_message(b'{"text":"hello"}')
    assert "Unable to parse message" in caplog.text


@pytest.mark.add_response(
    "/v1/user/me", "GET", get_response_path("gitter_connect.json"), status=200
)
@pytest.mark.add_response(
    "/v1/rooms/foo/chatMessages",
    "GET",
    get_response_path("gitter_message.json"),
    status=200,
)
@pytest.mark.add_response(
    "/v1/rooms/foo/chatMessages",
    "POST",
    get_response_path("gitter_send_message.json"),
    status=200,
)
@pytest.mark.asyncio
async def test_end_to_end(connector, opsdroid, mock_api, caplog):
    """Connect, recieve a message, trigger a skill and respond.

    - When opsdroid starts it will connect to gitter
    - When the connector starts listening it will get a message
    - That message should trigger the test_skill
    - The skill will respond and we check that in the logs
    """

    caplog.set_level(logging.INFO)

    @match_regex("hi")
    async def test_skill(opsdroid, config, event):
        assert event.text == "hi"
        logging.getLogger(__name__).info("test_skill called")
        await event.respond("hey there!")

    opsdroid.register_skill(test_skill, config={"name": "test"})

    async with running_opsdroid(opsdroid):
        assert connector.listening
        assert connector.bot_gitter_id == "12345"

        assert "test_skill called" in caplog.text
        assert "Successfully responded." in caplog.text

    assert not connector.listening


@pytest.mark.add_response(
    "/v1/user/me", "GET", get_response_path("gitter_connect.json"), status=200
)
@pytest.mark.add_response(
    "/v1/rooms/foo/chatMessages",
    "GET",
    get_response_path("gitter_message.json"),
    status=200,
)
@pytest.mark.add_response(
    "/v1/rooms/foo/chatMessages",
    "POST",
    get_response_path("gitter_send_message.json"),
    status=400,
)
@pytest.mark.asyncio
async def test_send_message_failure(connector, mock_api, caplog):
    caplog.set_level(logging.INFO)
    await connector.connect()
    await connector.send_message(
        Message(text="Hello world", target="foo", user="bar", connector=connector)
    )
    assert "Unable to respond." in caplog.text


@pytest.mark.add_response(
    "/v1/user/me", "GET", get_response_path("gitter_connect.json"), status=200
)
@pytest.mark.add_response(
    "/v1/rooms/foo/chatMessages",
    "GET",
    get_response_path("gitter_bot_message.json"),
    status=200,
)
@pytest.mark.asyncio
async def test_ignore_bot_message(connector, opsdroid, mock_api, caplog):
    """Ignore messages from self.

    If the ID in the ``/user/me`` call matches that in the message
    the message should be ignored and the skill is not triggered.
    """

    caplog.set_level(logging.INFO)

    @match_regex("hi")
    async def test_skill(opsdroid, config, event):
        logging.getLogger(__name__).info("test_skill called")

    opsdroid.register_skill(test_skill, config={"name": "test"})

    async with running_opsdroid(opsdroid):
        assert "test_skill called" not in caplog.text
