"""Tests for the ConnectorSlack class."""
import logging

import asynctest.mock as amock
import pytest
from opsdroid import events
from opsdroid.connector.slack.connector import SlackApiError
from opsdroid.connector.slack.events import (
    Blocks,
    EditedBlocks,
    ModalOpen,
    ModalPush,
    ModalUpdate,
)
from slack_sdk.socket_mode.request import SocketModeRequest

from .conftest import get_path

USERS_INFO = ("/users.info", "GET", get_path("method_users.info.json"), 200)
AUTH_TEST = ("/auth.test", "POST", get_path("method_auth.test.json"), 200)
CHAT_POST_MESSAGE = ("/chat.postMessage", "POST", {"ok": True}, 200)
CHAT_UPDATE_MESSAGE = ("/chat.update", "POST", {"ok": True}, 200)
VIEWS_OPEN = ("/views.open", "POST", {"ok": True}, 200)
VIEWS_UPDATE = ("/views.update", "POST", {"ok": True}, 200)
VIEWS_PUSH = ("/views.push", "POST", {"ok": True}, 200)
REACTIONS_ADD = ("/reactions.add", "POST", {"ok": True}, 200)
CONVERSATIONS_HISTORY = (
    "/conversations.history",
    "GET",
    get_path("method_conversations.history.json"),
    200,
)
CONVERSATIONS_LIST_LAST_PAGE = (
    "/conversations.list",
    "GET",
    get_path("method_conversations.list_last_page.json"),
    200,
)
CONVERSATIONS_CREATE = ("/conversations.create", "POST", {"ok": True}, 200)
CONVERSATIONS_RENAME = ("/conversations.rename", "POST", {"ok": True}, 200)
CONVERSATIONS_JOIN = ("/conversations.join", "POST", {"ok": True}, 200)
CONVERSATIONS_INVITE = ("/conversations.invite", "POST", {"ok": True}, 200)
CONVERSATIONS_SET_TOPIC = ("/conversations.setTopic", "POST", {"ok": True}, 200)
PINS_ADD = ("/pins.add", "POST", {"ok": True}, 200)
PINS_REMOVE = ("/pins.remove", "POST", {"ok": True}, 200)


@pytest.fixture
async def send_event(connector, mock_api):
    """Mock a send opsdroid event and return payload used and response from the request"""

    async def _send_event(api_call, event):
        api_endpoint, *_ = api_call
        response = await connector.send(event)
        payload = mock_api.get_payload(api_endpoint)

        return payload, response

    return _send_event


@pytest.mark.asyncio
@pytest.mark.add_response(*USERS_INFO)
@pytest.mark.add_response(*AUTH_TEST)
async def test_connect_events_api(connector, mock_api):
    await connector.connect()
    assert mock_api.called("/auth.test")
    assert mock_api.called("/users.info")
    connector.auth_info["user_id"] == "B061F7JD2"
    connector.user_info["user"] = "B061F7JD2"
    assert connector.bot_id == "B061F7JD2"


@pytest.mark.asyncio
@pytest.mark.add_response(*USERS_INFO)
@pytest.mark.add_response(*AUTH_TEST)
async def test_connect_socket_mode(opsdroid, mock_api_obj, mock_api):
    opsdroid.config["connectors"] = {
        "slack": {"bot-token": "abc123", "socket-mode": True, "app-token": "bcd456"}
    }
    await opsdroid.load()
    connector = opsdroid.get_connector("slack")
    connector.slack_web_client.base_url = mock_api_obj.base_url
    connector.socket_mode_client.connect = amock.CoroutineMock()
    await connector.connect()
    assert connector.socket_mode_client.connect.called
    await connector.disconnect()


@pytest.mark.asyncio
@pytest.mark.add_response(*USERS_INFO)
@pytest.mark.add_response(*AUTH_TEST)
async def test_connect_no_socket_mode_client(opsdroid, mock_api_obj, mock_api, caplog):
    opsdroid.config["connectors"] = {
        "slack": {"bot-token": "abc123", "socket-mode": True}
    }
    await opsdroid.load()
    connector = opsdroid.get_connector("slack")
    connector.slack_web_client.base_url = mock_api_obj.base_url
    await connector.connect()
    assert "RTM support has been dropped" in caplog.text
    await connector.disconnect()


@pytest.mark.asyncio
async def test_connect_failure(connector, mock_api, caplog):
    await connector.connect()
    assert "The Slack Connector will not be available" in caplog.text
    await connector.disconnect()


@pytest.mark.asyncio
async def test_disconnect(opsdroid, mock_api_obj, mock_api):
    opsdroid.config["connectors"] = {
        "slack": {"bot-token": "abc123", "socket-mode": True, "app-token": "bcd456"}
    }
    await opsdroid.load()
    connector = opsdroid.get_connector("slack")
    await connector.disconnect()
    connector.socket_mode_client.disconnect = amock.CoroutineMock()
    connector.socket_mode_client.close = amock.CoroutineMock()
    await connector.disconnect()
    assert connector.socket_mode_client.disconnect.called
    assert connector.socket_mode_client.close.called


@pytest.mark.asyncio
async def test_socket_event_handler(opsdroid, mock_api_obj, mock_api):
    opsdroid.config["connectors"] = {
        "slack": {"bot-token": "abc123", "socket-mode": True, "app-token": "bcd456"}
    }
    await opsdroid.load()
    connector = opsdroid.get_connector("slack")
    request = SocketModeRequest(
        type="mock", envelope_id="random-sring", payload={"type": "random_payload"}
    )
    connector.socket_mode_client.send_socket_mode_response = amock.CoroutineMock()
    await connector.socket_event_handler(connector.socket_mode_client, request)
    assert connector.socket_mode_client.send_socket_mode_response.called
    await connector.disconnect()


@pytest.mark.asyncio
@pytest.mark.add_response(
    "/users.info",
    "GET",
    {"ok": True, "user": {"id": "U01NK1K9L68", "name": "Test User"}},
    200,
)
async def test_lookup_username_user_not_present(connector, mock_api):
    user = await connector.lookup_username("U01NK1K9L68")
    assert mock_api.called("/users.info")
    assert user["id"] == "U01NK1K9L68"


@pytest.mark.asyncio
@pytest.mark.add_response(*CONVERSATIONS_HISTORY)
async def test_search_history_messages(connector, mock_api):
    history = await connector.search_history_messages(
        "C01N639ECTY", "1512085930.000000", "1512085980.000000"
    )
    assert mock_api.called("/conversations.history")
    assert len(history) == 2
    assert isinstance(history, list)


@pytest.mark.asyncio
@pytest.mark.add_response(*CONVERSATIONS_HISTORY)
async def test_search_history_messages_limit_more_than_1000(
    connector, mock_api, caplog
):
    caplog.set_level(logging.INFO)
    await connector.search_history_messages(
        "C01N639ECTY", "1512085930.000000", "1512085980.000000", 1001
    )
    assert mock_api.called("/conversations.history")
    assert "This might take some time" in caplog.text


@pytest.mark.asyncio
@pytest.mark.add_response(
    "/conversations.history",
    "GET",
    get_path("method_conversations.history_second_page.json"),
    200,
)
@pytest.mark.add_response(
    "/conversations.history",
    "GET",
    get_path("method_conversations.history_first_page.json"),
    200,
)
async def test_search_history_messages_more_than_one_api_request(connector, mock_api):
    history = await connector.search_history_messages(
        "C01N639ECTY", "1512085930.000000", "1512085980.000000"
    )
    assert mock_api.called("/conversations.history")
    assert len(history) == 4
    assert isinstance(history, list)


@pytest.mark.asyncio
@pytest.mark.add_response(*CONVERSATIONS_LIST_LAST_PAGE)
async def test_find_channel(connector, mock_api):
    connector.known_channels = {"general": {"name": "general", "id": "C012AB3CD"}}

    channel = await connector.find_channel("general")
    assert channel["id"] == "C012AB3CD"
    assert channel["name"] == "general"


@pytest.mark.asyncio
@pytest.mark.add_response(*CONVERSATIONS_LIST_LAST_PAGE)
async def test_find_channel_not_found(connector, mock_api, caplog):
    connector.known_channels = {"general": {"name": "general", "id": "C012AB3CD"}}

    caplog.set_level(logging.INFO)
    await connector.find_channel("another-channel")
    assert "Channel with name another-channel not found" in caplog.text


@pytest.mark.asyncio
async def test_replace_usernames(connector):
    connector.known_users = {"U01NK1K9L68": {"name": "Test User"}}
    message = "hello <@U01NK1K9L68>"
    replaced_message = await connector.replace_usernames(message)
    assert replaced_message == "hello Test User"


@pytest.mark.asyncio
@pytest.mark.add_response(*CHAT_POST_MESSAGE)
async def test_send_message(send_event, connector):
    event = events.Message(text="test", user="user", target="room", connector=connector)
    payload, response = await send_event(CHAT_POST_MESSAGE, event)
    assert payload == {
        "channel": "room",
        "text": "test",
        "username": "opsdroid",
        "icon_emoji": ":robot_face:",
    }
    assert response["ok"]


@pytest.mark.asyncio
@pytest.mark.add_response(*CHAT_POST_MESSAGE)
async def test_send_message_inside_thread(send_event, connector):
    linked_event = events.Message(
        text="linked text", raw_event={"thread_ts": "1582838099.000600"}
    )
    event = events.Message(
        text="test",
        user="user",
        target="room",
        connector=connector,
        linked_event=linked_event,
        event_id="1582838099.000601",
    )
    payload, response = await send_event(CHAT_POST_MESSAGE, event)
    assert payload == {
        "channel": "room",
        "text": "test",
        "username": "opsdroid",
        "icon_emoji": ":robot_face:",
        "thread_ts": "1582838099.000600",
    }
    assert response["ok"]


@pytest.mark.asyncio
@pytest.mark.add_response(*CHAT_POST_MESSAGE)
async def test_send_message_inside_thread_is_true(connector, send_event):
    connector.start_thread = True
    linked_event = events.Message(
        text="linked text", event_id="1582838099.000601", raw_event={}
    )
    event = events.Message(
        text="test",
        user="user",
        target="room",
        connector=connector,
        linked_event=linked_event,
    )
    payload, response = await send_event(CHAT_POST_MESSAGE, event)
    assert payload == {
        "channel": "room",
        "text": "test",
        "username": "opsdroid",
        "icon_emoji": ":robot_face:",
        "thread_ts": "1582838099.000601",
    }
    assert response["ok"]


@pytest.mark.asyncio
@pytest.mark.add_response(*CHAT_UPDATE_MESSAGE)
async def test_edit_message(send_event, connector):
    linked_event = "1582838099.000600"

    event = events.EditedMessage(
        text="edited_message",
        user="user",
        target="room",
        connector=connector,
        linked_event=linked_event,
    )

    payload, response = await send_event(CHAT_UPDATE_MESSAGE, event)

    assert payload == {
        "channel": "room",
        "ts": "1582838099.000600",
        "text": "edited_message",
    }
    assert response["ok"]


@pytest.mark.asyncio
@pytest.mark.add_response(*CHAT_POST_MESSAGE)
async def test_send_blocks(send_event, connector):
    event = Blocks(
        [{"type": "section", "text": {"type": "mrkdwn", "text": "*Test*"}}],
        target="room",
        connector=connector,
    )
    payload, response = await send_event(CHAT_POST_MESSAGE, event)
    assert payload == {
        "channel": "room",
        "username": "opsdroid",
        "blocks": '[{"type": "section", "text": {"type": "mrkdwn", "text": "*Test*"}}]',
        "icon_emoji": ":robot_face:",
    }
    assert response["ok"]


@pytest.mark.asyncio
@pytest.mark.add_response(*CHAT_UPDATE_MESSAGE)
async def test_edit_blocks(send_event, connector):
    event = EditedBlocks(
        [{"type": "section", "text": {"type": "mrkdwn", "text": "*Test*"}}],
        user="user",
        target="room",
        connector=connector,
        linked_event="1358878749.000002",
    )
    payload, response = await send_event(CHAT_UPDATE_MESSAGE, event)
    assert payload == {
        "channel": "room",
        "blocks": '[{"type": "section", "text": {"type": "mrkdwn", "text": "*Test*"}}]',
        "ts": "1358878749.000002",
    }
    assert response["ok"]


@pytest.mark.asyncio
@pytest.mark.add_response(*VIEWS_OPEN)
async def test_open_modal(send_event, connector):
    event = ModalOpen(trigger_id="123456", view={"key1": "value1", "key2": "value2"})
    payload, response = await send_event(VIEWS_OPEN, event)
    assert payload == {
        "trigger_id": "123456",
        "view": '{"key1": "value1", "key2": "value2"}',
    }
    assert response["ok"]


@pytest.mark.asyncio
@pytest.mark.add_response(*VIEWS_UPDATE)
async def test_update_modal(send_event, connector):
    event = ModalUpdate(
        external_id="123456",
        view={"key1": "value1", "key2": "value2"},
        hash_="12345678",
    )
    payload, response = await send_event(VIEWS_UPDATE, event)
    assert payload == {
        "external_id": "123456",
        "view": '{"key1": "value1", "key2": "value2"}',
        "hash": "12345678",
    }
    assert response["ok"]


@pytest.mark.asyncio
@pytest.mark.add_response(*VIEWS_PUSH)
async def test_push_modal(send_event, connector):
    event = ModalPush(trigger_id="123456", view={"key1": "value1", "key2": "value2"})
    payload, response = await send_event(VIEWS_PUSH, event)
    assert payload == {
        "trigger_id": "123456",
        "view": '{"key1": "value1", "key2": "value2"}',
    }
    assert response["ok"]


@pytest.mark.asyncio
@pytest.mark.add_response(*REACTIONS_ADD)
async def test_send_reaction(send_event, connector):
    message = events.Message(
        text="linked text",
        target="room",
        event_id="1582838099.000601",
        raw_event={"ts": 0},
    )
    event = events.Reaction("😀", target=message.target, linked_event=message)
    payload, response = await send_event(REACTIONS_ADD, event)
    assert payload == {
        "channel": "room",
        "name": "grinning_face",
        "timestamp": "1582838099.000601",
    }
    assert response["ok"]


@pytest.mark.asyncio
@pytest.mark.add_response(
    "/reactions.add", "POST", {"ok": False, "error": "invalid_name"}, 200
)
async def test_send_reaction_invalid_name(send_event):
    message = events.Message(
        text="linked text",
        target="room",
        event_id="1582838099.000601",
        raw_event={"ts": 0},
    )
    event = events.Reaction("NOT_EMOJI", target=message.target, linked_event=message)
    await send_event(("/reactions.add",), event)


@pytest.mark.asyncio
@pytest.mark.add_response("/reactions.add", "POST", {"ok": False}, 200)
async def test_send_reaction_unknown_error(send_event):
    message = events.Message(
        text="linked text",
        target="room",
        event_id="1582838099.000601",
        raw_event={"ts": 0},
    )
    event = events.Reaction("NOT_EMOJI", target=message.target, linked_event=message)
    with pytest.raises(SlackApiError):
        _, response = await send_event(("/reactions.add",), event)
        assert not response["ok"]


@pytest.mark.asyncio
@pytest.mark.add_response(*CONVERSATIONS_CREATE)
async def test_send_room_creation(send_event):
    event = events.NewRoom(name="new_room")
    payload, response = await send_event(CONVERSATIONS_CREATE, event)
    assert payload == {"name": "new_room"}
    assert response["ok"]


@pytest.mark.asyncio
@pytest.mark.add_response(*CONVERSATIONS_RENAME)
async def test_send_room_name_set(send_event):
    event = events.RoomName(name="new_name_room", target="room")
    payload, response = await send_event(CONVERSATIONS_RENAME, event)
    assert payload == {"name": "new_name_room", "channel": "room"}
    assert response["ok"]


@pytest.mark.asyncio
@pytest.mark.add_response(*CONVERSATIONS_JOIN)
async def test_join_room(send_event):
    event = events.JoinRoom(target="room")
    payload, response = await send_event(CONVERSATIONS_JOIN, event)
    assert payload == {"channel": "room"}
    assert response["ok"]


@pytest.mark.asyncio
@pytest.mark.add_response(*CONVERSATIONS_INVITE)
async def test_send_user_invitation(send_event):
    event = events.UserInvite(user_id="U2345678901", target="room")
    payload, response = await send_event(CONVERSATIONS_INVITE, event)
    assert payload == {"channel": "room", "users": "U2345678901"}
    assert response["ok"]


@pytest.mark.asyncio
@pytest.mark.add_response(*CONVERSATIONS_SET_TOPIC)
async def test_send_room_description(send_event):
    event = events.RoomDescription(description="Topic Update", target="room")
    payload, response = await send_event(CONVERSATIONS_SET_TOPIC, event)
    assert payload == {"channel": "room", "topic": "Topic Update"}
    assert response["ok"]


@pytest.mark.asyncio
@pytest.mark.add_response(*PINS_ADD)
async def test_send_pin_added(send_event, connector):
    message = events.Message(
        "An important message",
        user="User McUserface",
        user_id="U9S8JGF45",
        target="room",
        connector=connector,
        event_id="1582838099.000600",
    )

    event = events.PinMessage(target="room", linked_event=message)

    payload, response = await send_event(PINS_ADD, event)
    assert payload == {"channel": "room", "timestamp": "1582838099.000600"}
    assert response["ok"]


@pytest.mark.asyncio
@pytest.mark.add_response(*PINS_REMOVE)
async def test_send_pin_removed(send_event, connector):
    message = events.Message(
        "An important message",
        user="User McUserface",
        user_id="U9S8JGF45",
        target="an-existing-room",
        connector=connector,
        event_id="1582838099.000600",
    )

    event = events.UnpinMessage(target="room", linked_event=message)

    payload, response = await send_event(PINS_REMOVE, event)
    assert payload == {"channel": "room", "timestamp": "1582838099.000600"}
    assert response["ok"]
