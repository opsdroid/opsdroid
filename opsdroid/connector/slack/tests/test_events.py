"""Test events from Slack"""

import pytest
from opsdroid.connector.slack.events import InteractiveAction
from opsdroid.events import Message
from opsdroid.testing import MINIMAL_CONFIG, running_opsdroid


@pytest.mark.anyio
@pytest.mark.add_response("/", "POST", {"ok": True}, 200)
async def test_respond_response_url_exists(mock_api_obj, mock_api):
    action = InteractiveAction({"response_url": mock_api_obj.base_url})
    response = await action.respond("this is a test response")
    assert response["ok"]


@pytest.mark.anyio
@pytest.mark.add_response("/", "POST", "ok", 200)
async def test_respond_response_text_content_type(mock_api_obj, mock_api):
    action = InteractiveAction({"response_url": mock_api_obj.base_url})
    response = await action.respond("this is a test response")
    assert response == "ok"


@pytest.mark.anyio
async def test_respond_event_response_url_does_not_exist(mock_api_obj, mock_api):
    action = InteractiveAction({})
    response = await action.respond("this is a test response")
    assert response == {"error": "Response URL not available in payload."}


@pytest.mark.anyio
@pytest.mark.add_response("/", "POST", {"ok": True}, 200)
async def test_respond_response_event_not_a_string(opsdroid, mock_api_obj, mock_api):
    await opsdroid.load(config=MINIMAL_CONFIG)
    async with running_opsdroid(opsdroid):
        action = InteractiveAction({"response_url": mock_api_obj.base_url})
        message = Message("this is a test response")
        response = await action.respond(message)
        assert response


@pytest.mark.anyio
@pytest.mark.add_response("/", "POST", {"ok": True}, 200)
async def test_respond_response_type_defaults_to_in_channel(mock_api_obj, mock_api):
    action = InteractiveAction({"response_url": mock_api_obj.base_url})
    response = await action.respond("this is a test response")
    assert response["ok"]
    assert mock_api.get_payload("/")["response_type"] == "in_channel"


@pytest.mark.anyio
@pytest.mark.add_response("/", "POST", {"ok": True}, 200)
async def test_respond_response_type_ephemeral_kwarg(mock_api_obj, mock_api):
    action = InteractiveAction({"response_url": mock_api_obj.base_url})
    response = await action.respond("only visible to you", response_type="ephemeral")
    assert response["ok"]
    payload = mock_api.get_payload("/")
    assert payload["response_type"] == "ephemeral"
    assert payload["text"] == "only visible to you"


@pytest.mark.anyio
@pytest.mark.add_response("/", "POST", {"ok": True}, 200)
async def test_respond_response_type_from_connector_config(
    connector, mock_api_obj, mock_api
):
    connector.response_type = "ephemeral"
    action = InteractiveAction(
        {"response_url": mock_api_obj.base_url}, connector=connector
    )
    response = await action.respond("only visible to you")
    assert response["ok"]
    assert mock_api.get_payload("/")["response_type"] == "ephemeral"


@pytest.mark.anyio
@pytest.mark.add_response("/", "POST", {"ok": True}, 200)
async def test_respond_response_type_kwarg_overrides_connector_config(
    connector, mock_api_obj, mock_api
):
    connector.response_type = "ephemeral"
    action = InteractiveAction(
        {"response_url": mock_api_obj.base_url}, connector=connector
    )
    response = await action.respond("visible to everyone", response_type="in_channel")
    assert response["ok"]
    assert mock_api.get_payload("/")["response_type"] == "in_channel"
