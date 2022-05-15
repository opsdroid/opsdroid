"""Test receive events that come from the Slack API.
Depending on payload different methods from create_events module will be tested
"""
import json

import pytest
from opsdroid.connector.slack.create_events import SlackEventCreator
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


@pytest.mark.asyncio
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


@pytest.mark.asyncio
async def test__create_user_name_user_not_found(connector, mock_api):
    event_creator = SlackEventCreator(connector=connector)
    user_name = await event_creator._get_user_name({})
    assert not user_name


@pytest.mark.asyncio
async def test_create_message_user_name_not_found(connector, mock_api):
    event_creator = SlackEventCreator(connector=connector)
    message = await event_creator.create_message({}, None)
    assert not message


@pytest.mark.asyncio
async def test_edit_message_user_name_not_found(connector, mock_api):
    event_creator = SlackEventCreator(connector=connector)
    message = await event_creator.edit_message({"message": {}}, None)
    assert not message
