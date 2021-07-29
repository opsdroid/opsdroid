import mock
import pytest
import vcr

import logging
from pathlib import Path

from opsdroid.connector.teams import TeamsConnector
from opsdroid.events import Message
from opsdroid.matchers import match_regex
from opsdroid.testing import call_endpoint, running_opsdroid


def get_response_path(response):
    return Path(__file__).parent / "responses" / response


@pytest.fixture
async def connector(opsdroid, mock_api_obj):
    opsdroid.config["connectors"] = {
        "teams": {
            "app-id": "abc123",
            "password": "def456",
        }
    }
    await opsdroid.load()
    return opsdroid.get_connector("teams")


def test_teams_init():
    connector = TeamsConnector({})
    assert connector.name == "teams"


@pytest.mark.asyncio
async def test_connect(connector, mock_api):
    await connector.connect()

    assert connector.service_endpoints == {}


@pytest.mark.asyncio
async def test_parse_channel_id(connector, mock_api):
    valid_ids = [
        "https://teams.microsoft.com/l/channel/abc123",
        "abc123",
    ]
    for id in valid_ids:
        assert connector.parse_channel_id(id) == "abc123"


@pytest.mark.asyncio
@vcr.use_cassette(
    "opsdroid/connector/teams/tests/test_ping_pong.yaml",
    record_mode="once",
    filter_post_data_parameters=["client_id", "client_secret"],
    ignore_localhost=True,
)
async def test_ping_pong(opsdroid, connector, mock_api, mock_api_obj, caplog):
    """Test a message is received and response is sent."""
    caplog.set_level(logging.INFO)

    @match_regex(r"ping")
    async def test_skill(opsdroid, config, event):
        assert event.connector.name == "teams"
        assert event.text == "ping"

        logging.getLogger(__name__).info("ping called")
        await event.respond("pong")

        # Send message to the room with a string target too
        [target, *_] = event.target.conversation.id.split(";")
        msg = Message(
            text="pong",
            target=target,
        )
        await event.connector.send(msg)

    opsdroid.register_skill(test_skill, config={"name": "test"})

    with mock.patch("uuid.uuid1") as mock_uuid:
        mock_uuid.return_value = "ca153e8e-ed8c-11eb-9208-1e2940309485"
        async with running_opsdroid(opsdroid):
            with open(get_response_path("teams_ping_payload.json"), "r") as fh:
                data = fh.read()

                resp = await call_endpoint(
                    opsdroid,
                    "/connector/teams",
                    "POST",
                    data=data,
                    headers={"Content-Type": "application/json"},
                )
                assert resp.status == 200
                assert "ping called" in caplog.text


@pytest.mark.asyncio
async def test_invalid_calls(opsdroid, connector, mock_api, mock_api_obj, caplog):
    caplog.set_level(logging.INFO)

    @match_regex(r"ping")
    async def test_skill(opsdroid, config, event):
        pass

    opsdroid.register_skill(test_skill, config={"name": "test"})

    async with running_opsdroid(opsdroid):
        resp = await call_endpoint(
            opsdroid,
            "/connector/teams",
            "POST",
            data={},
            headers={"Content-Type": "application/text"},
        )
        assert resp.status == 415

        with open(get_response_path("teams_invalid_message.json"), "r") as fh:
            data = fh.read()

            resp = await call_endpoint(
                opsdroid,
                "/connector/teams",
                "POST",
                data=data,
                headers={"Content-Type": "application/json"},
            )
            assert resp.status == 200
            assert "Recieved invalid activity" in caplog.text


@pytest.mark.asyncio
async def test_send_message_to_invalid_target(
    opsdroid, connector, mock_api, mock_api_obj, caplog
):
    caplog.set_level(logging.INFO)

    @match_regex(r"ping")
    async def test_skill(opsdroid, config, event):
        pass

    opsdroid.register_skill(test_skill, config={"name": "test"})

    async with running_opsdroid(opsdroid):
        await connector.send(Message("hello", target=None, connector=connector))
        assert "not a valid place to send a message" in caplog.text


@pytest.mark.asyncio
async def test_send_message_to_room_not_spoken_in(
    opsdroid, connector, mock_api, mock_api_obj, caplog
):
    caplog.set_level(logging.INFO)

    @match_regex(r"ping")
    async def test_skill(opsdroid, config, event):
        pass

    opsdroid.register_skill(test_skill, config={"name": "test"})

    async with running_opsdroid(opsdroid):
        await connector.send(Message("hello", target="foo_room", connector=connector))
        assert "Unable to send a message" in caplog.text
