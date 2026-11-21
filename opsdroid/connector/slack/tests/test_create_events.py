"""Test receive events that come from the Slack API.
Depending on payload different methods from create_events module will be tested
"""

import json
from unittest.mock import AsyncMock

import pytest
from opsdroid.connector.slack.create_events import SlackEventCreator
from opsdroid.events import EditedMessage, Message
from opsdroid.testing import MINIMAL_CONFIG, call_endpoint, run_unit_test

from .conftest import get_path


def get_webhook_payload(file_name, _type):
    """Convert a file into a webhook payload. Return headers and payload"""
    with open(get_path(file_name), "r") as _file:
        if _type == "json":
            headers = {"content-type": "application/json"}

            return headers, json.dumps(json.load(_file))

        if _type == "urlencoded":
            headers = {"content-type": "application/x-www-form-urlencoded"}

            return headers, _file.read()


CONNECTOR_ENDPOINT = "/connector/slack"

# The following are sample responses from the Slack API, when the Slack connector is initializing
USERS_INFO = ("/users.info", "GET", get_path("method_users.info.json"), 200)
AUTH_TEST = ("/auth.test", "POST", get_path("method_auth.test.json"), 200)
CONVERSATIONS_LIST_LAST_PAGE = (
    "/conversations.list",
    "GET",
    get_path("method_conversations.list_last_page.json"),
    200,
)
CONVERSATIONS_LIST_FIRST_PAGE = (
    "/conversations.list",
    "GET",
    get_path("method_conversations.list_first_page.json"),
    200,
)


@pytest.mark.anyio
@pytest.mark.parametrize(
    "payload",
    [
        "payload_url_verification.json",
        "payload_message.json",
        "payload_message_bot_message.json",
        "payload_message_message_changed.json",
        "payload_message_channel_join.json",
        "payload_channel_created.json",
        "payload_channel_archive.json",
        "payload_channel_unarchive.json",
        "payload_team_join.json",
        "payload_channel_rename.json",
        "payload_pin_added.json",
        "payload_pin_removed.json",
        "payload_block_action_button.urlencoded",
        "payload_block_action_overflow.urlencoded",
        "payload_block_action_static_select.urlencoded",
        "payload_block_action_datepicker.urlencoded",
        "payload_block_action_multi_static_select.urlencoded",
        "payload_message_action.urlencoded",
        "payload_slash_command.urlencoded",
        "payload_view_submission.urlencoded",
    ],
)
@pytest.mark.add_response(*USERS_INFO)
@pytest.mark.add_response(*AUTH_TEST)
@pytest.mark.add_response(*CONVERSATIONS_LIST_LAST_PAGE)
@pytest.mark.add_response(*CONVERSATIONS_LIST_FIRST_PAGE)
async def test_events_from_slack(opsdroid, connector, mock_api, payload):
    """Mocks receiving a payload event from the Slack API.
    Run unit test against an opsdroid instance
    parameter:
        payload: file name with the slack api payload for a particular event

    """
    await opsdroid.load(config=MINIMAL_CONFIG)

    connector.known_users = {
        "U01NK1K9L68": {"name": "Test User"},
        "U01P7131BA4": {"name": "Another User"},
    }

    async def receive_event(payload):
        payload_type = payload.split(".")[1]

        headers, data = get_webhook_payload(payload, payload_type)
        resp = await call_endpoint(
            opsdroid,
            CONNECTOR_ENDPOINT,
            "POST",
            data=data,
            headers=headers,
        )
        assert resp.status == 200

        return True

    assert await run_unit_test(opsdroid, receive_event, payload)


@pytest.mark.anyio
async def test__create_user_name_user_not_found(connector, mock_api):
    event_creator = SlackEventCreator(connector=connector)
    user_name = await event_creator._get_user_name({})
    assert not user_name


@pytest.mark.anyio
async def test_create_message_user_name_not_found(connector, mock_api):
    event_creator = SlackEventCreator(connector=connector)
    message = await event_creator.create_message({}, None)
    assert not message


@pytest.mark.anyio
async def test_edit_message_user_name_not_found(connector, mock_api):
    event_creator = SlackEventCreator(connector=connector)
    message = await event_creator.edit_message({"message": {}}, None)
    assert not message


# --- Regression tests for issue #2000 -------------------------------------
# Opsdroid must not react to Slack messages that are only visible to a
# single user (ephemeral / hidden messages) or to system message subtypes,
# while normal messages must still be parsed.


def _wrap_event(event):
    """Wrap a raw slack event in an event_callback payload."""
    return {"type": "event_callback", "event": event}


@pytest.mark.anyio
async def test_event_handler_normal_message(connector, mock_api):
    """A normal channel message should be parsed into a Message event."""
    connector.known_users = {"U01NK1K9L68": {"name": "Test User"}}
    connector.opsdroid.parse = AsyncMock()

    await connector.event_handler(
        _wrap_event(
            {
                "type": "message",
                "text": "hello opsdroid",
                "user": "U01NK1K9L68",
                "channel": "C01N9PM1D53",
                "ts": "1613632675.006300",
            }
        )
    )

    connector.opsdroid.parse.assert_called_once()
    event = connector.opsdroid.parse.call_args[0][0]
    assert isinstance(event, Message)
    assert event.text == "hello opsdroid"


@pytest.mark.anyio
async def test_event_handler_skips_hidden_ephemeral_message(connector, mock_api):
    """Messages only visible to one user (hidden/ephemeral) must be skipped."""
    connector.known_users = {"U01NK1K9L68": {"name": "Test User"}}
    connector.opsdroid.parse = AsyncMock()

    await connector.event_handler(
        _wrap_event(
            {
                "type": "message",
                "hidden": True,
                "text": "only visible to me",
                "user": "U01NK1K9L68",
                "channel": "C01N9PM1D53",
                "ts": "1613632675.006300",
            }
        )
    )

    connector.opsdroid.parse.assert_not_called()


@pytest.mark.anyio
async def test_event_handler_skips_ephemeral_subtype(connector, mock_api):
    """Messages with an ephemeral subtype must be skipped."""
    connector.known_users = {"U01NK1K9L68": {"name": "Test User"}}
    connector.opsdroid.parse = AsyncMock()

    await connector.event_handler(
        _wrap_event(
            {
                "type": "message",
                "subtype": "ephemeral",
                "text": "only visible to me",
                "user": "U01NK1K9L68",
                "channel": "C01N9PM1D53",
                "ts": "1613632675.006300",
            }
        )
    )

    connector.opsdroid.parse.assert_not_called()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "subtype",
    ["message_deleted", "message_replied", "channel_leave", "file_comment"],
)
async def test_event_handler_skips_system_message_subtypes(
    connector, mock_api, subtype
):
    """System message subtypes must be skipped instead of crashing/parsing."""
    connector.known_users = {"U01NK1K9L68": {"name": "Test User"}}
    connector.opsdroid.parse = AsyncMock()

    await connector.event_handler(
        _wrap_event(
            {
                "type": "message",
                "subtype": subtype,
                "text": "system message",
                "user": "U01NK1K9L68",
                "channel": "C01N9PM1D53",
                "ts": "1613632675.006300",
                "previous_message": {"text": "old"},
            }
        )
    )

    connector.opsdroid.parse.assert_not_called()


@pytest.mark.anyio
async def test_event_handler_skips_own_bot_message(connector, mock_api):
    """Messages posted by opsdroid itself must be skipped."""
    connector.bot_id = "B01MY4ZRP5M"
    connector.known_bots = {"B01MY4ZRP5M": {"id": "B01MY4ZRP5M"}}
    connector.opsdroid.parse = AsyncMock()

    await connector.event_handler(
        _wrap_event(
            {
                "type": "message",
                "subtype": "bot_message",
                "text": "Hi opsdroid",
                "bot_id": "B01MY4ZRP5M",
                "channel": "C01N9PM1D53",
                "ts": "1614540108.001500",
            }
        )
    )

    connector.opsdroid.parse.assert_not_called()


@pytest.mark.anyio
async def test_event_handler_skips_own_message_changed(connector, mock_api):
    """message_changed events caused by opsdroid's own edits must be skipped."""
    connector.bot_id = "B061F7JD2"
    connector.known_bots = {"B061F7JD2": {"id": "B061F7JD2"}}
    connector.opsdroid.parse = AsyncMock()

    await connector.event_handler(
        _wrap_event(
            {
                "type": "message",
                "subtype": "message_changed",
                "hidden": True,
                "message": {
                    "type": "message",
                    "text": "edited by the bot",
                    "bot_id": "B061F7JD2",
                    "ts": "1613632675.006300",
                },
                "channel": "C01N9PM1D53",
                "ts": "1613632704.006400",
            }
        )
    )

    connector.opsdroid.parse.assert_not_called()


@pytest.mark.anyio
async def test_event_handler_user_message_changed(connector, mock_api):
    """message_changed events from users should still create EditedMessage."""
    connector.known_users = {"U01NK1K9L68": {"name": "Test User"}}
    connector.opsdroid.parse = AsyncMock()

    await connector.event_handler(
        _wrap_event(
            {
                "type": "message",
                "subtype": "message_changed",
                "hidden": True,
                "message": {
                    "type": "message",
                    "text": "this is an edited message",
                    "user": "U01NK1K9L68",
                    "ts": "1613632675.006300",
                },
                "channel": "C01N9PM1D53",
                "ts": "1613632704.006400",
            }
        )
    )

    connector.opsdroid.parse.assert_called_once()
    event = connector.opsdroid.parse.call_args[0][0]
    assert isinstance(event, EditedMessage)
    assert event.text == "this is an edited message"
