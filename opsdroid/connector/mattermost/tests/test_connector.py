"""Tests for the ConnectorMattermost class."""
import pytest
import aiohttp.client_exceptions
import asyncio
from opsdroid.events import Message

from .conftest import get_path

pytestmark = pytest.mark.anyio

GET_USER_ME_SUCCESS = (
    "/api/v4/users/me",
    "GET",
    get_path("users.me.success.json"),
    200,
)
GET_USER_ME_ERROR = ("/api/v4/users/me", "GET", None, 401)

WEBSOCKET_HELLO = (
    "/api/v4/websocket",
    "WEBSOCKET",
    get_path("websocket/websocket.success.json"),
    200,
)

GET_CHANNEL_ID_FOR_CHANNEL_SUCCESS = (
    "/api/v4/teams/name/opsdroid/channels/name/unit_test_channel",
    "GET",
    get_path("teams.opsdroid.channel.unit_test_channel.success.json"),
    200,
)
CREATE_POST_SUCCESS = ("/api/v4/posts", "POST", None, 200)


@pytest.fixture
async def send_event(connector, mock_api):
    """Mock a send opsdroid event and return payload used and response from the request"""

    async def _send_event(api_call, event):
        api_endpoint, *_ = api_call
        response = await connector.send(event)
        payload = mock_api.get_payload(api_endpoint)

        return payload, response

    return _send_event


async def assert_websocket(func):
    retries = 10
    for i in range(retries):
        await asyncio.sleep(
            0.01
        )  # wait for the websocket event loop to catch up before checking its log outputs
        try:
            assert func()
        except Exception:
            if i + 1 >= retries:
                raise
            continue


@pytest.mark.add_response(*GET_USER_ME_SUCCESS)
@pytest.mark.add_response(*WEBSOCKET_HELLO)
async def test_api_key_success(connector, mock_api, caplog):
    """Test that creating without an API key raises an error."""
    caplog.set_level(
        "INFO"
    )  # cannot use 'with caplog.at_level' because it wouldn't apply to the websocket loop
    await connector.connect()
    asyncio.get_event_loop().create_task(
        connector.listen(), name="Unit Test Websocket task"
    )

    assert connector._bot_id == "test1234"
    assert connector._bot_name == "test_1234_account"

    whoami_call = mock_api.get_request("/api/v4/users/me", "GET", 0)
    assert "Authorization" in whoami_call.headers
    assert whoami_call.headers["Authorization"] == "Bearer unittest_token"

    assert "Connected as test_1234_account" in caplog.text
    await assert_websocket(
        lambda: "Mattermost Websocket authentification OK" in caplog.text
    )


@pytest.mark.add_response(*GET_USER_ME_ERROR)
async def test_api_key_failure(connector, mock_api, caplog):
    """Test that using an API key that Mattermost declares as Unauthorized, raises an error."""
    try:
        with caplog.at_level("ERROR"):
            await connector.connect()
            assert False
    except aiohttp.client_exceptions.ClientResponseError as ex:
        assert ex.status == 401

    assert connector._bot_id is None

    whoami_call = mock_api.get_request("/api/v4/users/me", "GET", 0)
    assert "Authorization" in whoami_call.headers
    assert whoami_call.headers["Authorization"] == "Bearer unittest_token"

    assert "Failed connecting to Mattermost" in caplog.text


@pytest.mark.add_response(*GET_USER_ME_SUCCESS)
@pytest.mark.add_response(*GET_CHANNEL_ID_FOR_CHANNEL_SUCCESS)
@pytest.mark.add_response(*CREATE_POST_SUCCESS)
async def test_api_send_message(connector, mock_api, caplog):
    """Test that using an API key that Mattermost declares as Unauthorized, raises an error."""
    with caplog.at_level("DEBUG"):
        await connector.connect()
        await connector.send_message(
            Message(text="Unit Test Message", target="unit_test_channel")
        )

    assert (
        "Querying channel for team 'opsdroid' and name 'unit_test_channel'"
        in caplog.text
    )
    assert (
        "Responding with: 'Unit Test Message' in room  unit_test_channel" in caplog.text
    )

    post_call = mock_api.get_payload("/api/v4/posts", 0)

    assert post_call["channel_id"] == "channel_id_for_name"
    assert post_call["message"] == "Unit Test Message"

    assert (
        "Sending post with payload '{'channel_id': 'channel_id_for_name', 'message': 'Unit Test Message'}'"
        in caplog.text
    )


@pytest.mark.add_response(*GET_USER_ME_SUCCESS)
@pytest.mark.add_response(*GET_CHANNEL_ID_FOR_CHANNEL_SUCCESS)
@pytest.mark.add_response(*CREATE_POST_SUCCESS)
async def test_api_send_message_threaded_new(connector, mock_api, caplog):
    """Test that Mattermost correctly creates a new thread if configured appropriately."""
    connector._use_threads = True

    with caplog.at_level("DEBUG"):
        await connector.connect()
        await connector.send_message(
            Message(
                text="Unit Test Message",
                target="unit_test_channel",
                linked_event=Message(
                    "Original Message",
                    raw_event={"data": {"post": '{"id": "top-level-id"}'}},
                ),
            )
        )

    assert (
        "Querying channel for team 'opsdroid' and name 'unit_test_channel'"
        in caplog.text
    )
    assert (
        "Responding with: 'Unit Test Message' in room  unit_test_channel" in caplog.text
    )

    post_call = mock_api.get_payload("/api/v4/posts", 0)

    assert post_call["channel_id"] == "channel_id_for_name"
    assert post_call["message"] == "Unit Test Message"

    assert (
        "Sending post with payload '{'channel_id': 'channel_id_for_name', 'message': 'Unit Test Message', 'root_id': 'top-level-id'}'"
        in caplog.text
    )


@pytest.mark.add_response(*GET_USER_ME_SUCCESS)
@pytest.mark.add_response(*GET_CHANNEL_ID_FOR_CHANNEL_SUCCESS)
@pytest.mark.add_response(*CREATE_POST_SUCCESS)
async def test_api_send_message_threaded_existing(connector, mock_api, caplog):
    """Test that Mattermost correctly creates a new thread if configured appropriately."""
    connector._use_threads = True

    with caplog.at_level("DEBUG"):
        await connector.connect()
        await connector.send_message(
            Message(
                text="Unit Test Message",
                target="unit_test_channel",
                linked_event=Message(
                    "Original Message",
                    raw_event={
                        "data": {
                            "post": '{"id": "inside-thread-id", "root_id": "top-level-id"}'
                        }
                    },
                ),
            )
        )

    assert (
        "Querying channel for team 'opsdroid' and name 'unit_test_channel'"
        in caplog.text
    )
    assert (
        "Responding with: 'Unit Test Message' in room  unit_test_channel" in caplog.text
    )

    post_call = mock_api.get_payload("/api/v4/posts", 0)

    assert post_call["channel_id"] == "channel_id_for_name"
    assert post_call["message"] == "Unit Test Message"

    assert (
        "Sending post with payload '{'channel_id': 'channel_id_for_name', 'message': 'Unit Test Message', 'root_id': 'top-level-id'}'"
        in caplog.text
    )


@pytest.mark.add_response(*GET_USER_ME_SUCCESS)
@pytest.mark.add_response(
    "/api/v4/websocket",
    "WEBSOCKET",
    get_path("websocket/message/mentioned/websocket.json"),
    200,
)
@pytest.mark.add_response(*WEBSOCKET_HELLO)
async def test_websocket_message_mentioned(connector, mock_api, caplog):
    """Tests that messages over the websocket are properly processed by opsdroid."""
    caplog.set_level(
        "DEBUG"
    )  # cannot use 'with caplog.at_level' because it wouldn't apply to the websocket loop
    await connector.connect()
    asyncio.get_event_loop().create_task(
        connector.listen(), name="Unit Test Websocket task"
    )

    await assert_websocket(lambda: "Processing raw Mattermost message" in caplog.text)

    await assert_websocket(
        lambda: "Message arrived in Unit Test skill: '@test_1234_account Unit Test Message'"
        in caplog.text
    )


@pytest.mark.add_response(*GET_USER_ME_SUCCESS)
@pytest.mark.add_response(
    "/api/v4/websocket",
    "WEBSOCKET",
    get_path("websocket/message/direct/websocket.json"),
    200,
)
@pytest.mark.add_response(*WEBSOCKET_HELLO)
async def test_websocket_message_direct(connector, mock_api, caplog):
    """Tests that messages over the websocket are properly processed by opsdroid."""
    caplog.set_level(
        "DEBUG"
    )  # cannot use 'with caplog.at_level' because it wouldn't apply to the websocket loop
    await connector.connect()
    asyncio.get_event_loop().create_task(
        connector.listen(), name="Unit Test Websocket task"
    )

    await assert_websocket(lambda: "Processing raw Mattermost message" in caplog.text)

    await assert_websocket(
        lambda: "Message arrived in Unit Test skill: 'Unit Test Message'" in caplog.text
    )


@pytest.mark.add_response(*GET_USER_ME_SUCCESS)
@pytest.mark.add_response(
    "/api/v4/websocket",
    "WEBSOCKET",
    get_path("websocket/message/unmentioned/websocket.json"),
    200,
)
@pytest.mark.add_response(*WEBSOCKET_HELLO)
async def test_websocket_message_unmentioned(connector, mock_api, caplog):
    """Tests that messages over the websocket are ignored if the bot was not mentioned in a proper channel."""
    caplog.set_level(
        "DEBUG"
    )  # cannot use 'with caplog.at_level' because it wouldn't apply to the websocket loop
    await connector.connect()
    asyncio.get_event_loop().create_task(
        connector.listen(), name="Unit Test Websocket task"
    )

    await assert_websocket(lambda: "Processing raw Mattermost message" in caplog.text)

    await assert_websocket(
        lambda: "Not a direct message and I am not mentioned: ignoring message"
        in caplog.text
    )

    await assert_websocket(
        lambda: "Message arrived in Unit Test skill" not in caplog.text
    )


@pytest.mark.add_response(*GET_USER_ME_SUCCESS)
@pytest.mark.add_response(
    "/api/v4/websocket",
    "WEBSOCKET",
    get_path("websocket/message/self/websocket.json"),
    200,
)
@pytest.mark.add_response(*WEBSOCKET_HELLO)
async def test_websocket_message_self(connector, mock_api, caplog):
    """Tests that messages over the websocket are ignored if the bot was not mentioned in a proper channel."""
    caplog.set_level(
        "DEBUG"
    )  # cannot use 'with caplog.at_level' because it wouldn't apply to the websocket loop
    await connector.connect()
    asyncio.get_event_loop().create_task(
        connector.listen(), name="Unit Test Websocket task"
    )

    await assert_websocket(lambda: "Processing raw Mattermost message" in caplog.text)

    await assert_websocket(lambda: "I am the author: ignoring message" in caplog.text)

    await assert_websocket(
        lambda: "Message arrived in Unit Test skill" not in caplog.text
    )


@pytest.mark.add_response(
    "/api/v4/channels/789",
    "GET",
    get_path("websocket/reaction/first/channels.789.json"),
    200,
)
@pytest.mark.add_response(
    "/api/v4/posts/456", "GET", get_path("websocket/reaction/first/posts.456.json"), 200
)
@pytest.mark.add_response(
    "/api/v4/users/123", "GET", get_path("websocket/users.123.json"), 200
)
@pytest.mark.add_response(*GET_USER_ME_SUCCESS)
@pytest.mark.add_response(
    "/api/v4/websocket",
    "WEBSOCKET",
    get_path("websocket/reaction/first/websocket.json"),
    200,
)
@pytest.mark.add_response(*WEBSOCKET_HELLO)
async def test_websocket_reaction_first(connector, mock_api, caplog):
    """Tests that messages over the websocket are propery processed by opsdroid."""

    connector._emoji_trigger = "emoji_test"

    caplog.set_level(
        "DEBUG"
    )  # cannot use 'with caplog.at_level' because it wouldn't apply to the websocket loop
    await connector.connect()
    asyncio.get_event_loop().create_task(
        connector.listen(), name="Unit Test Websocket task"
    )
    await assert_websocket(lambda: "Processing raw Mattermost message" in caplog.text)

    print("CAPLOG TEXT: ", caplog.text)

    await assert_websocket(lambda: "Message arrived in Unit Test skill" in caplog.text)


@pytest.mark.add_response(
    "/api/v4/channels/789",
    "GET",
    get_path("websocket/reaction/second/channels.789.json"),
    200,
)
@pytest.mark.add_response(
    "/api/v4/posts/456",
    "GET",
    get_path("websocket/reaction/second/posts.456.json"),
    200,
)
@pytest.mark.add_response(
    "/api/v4/users/123", "GET", get_path("websocket/users.123.json"), 200
)
@pytest.mark.add_response(*GET_USER_ME_SUCCESS)
@pytest.mark.add_response(
    "/api/v4/websocket",
    "WEBSOCKET",
    get_path("websocket/reaction/second/websocket.json"),
    200,
)
@pytest.mark.add_response(*WEBSOCKET_HELLO)
async def test_websocket_reaction_second(connector, mock_api, caplog):
    """Tests that messages over the websocket are propery processed by opsdroid."""

    connector._emoji_trigger = "emoji_test"

    caplog.set_level(
        "DEBUG"
    )  # cannot use 'with caplog.at_level' because it wouldn't apply to the websocket loop
    await connector.connect()
    asyncio.get_event_loop().create_task(
        connector.listen(), name="Unit Test Websocket task"
    )
    await assert_websocket(lambda: "Processing raw Mattermost message" in caplog.text)

    await assert_websocket(
        lambda: "Reaction is not the first of its kind: ignoring message" in caplog.text
    )

    await assert_websocket(
        lambda: "Message arrived in Unit Test skill" not in caplog.text
    )
