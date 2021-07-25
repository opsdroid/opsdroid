import mock
import pytest
import vcr

import logging
from pathlib import Path

from opsdroid.connector.teams import TeamsConnector
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
@vcr.use_cassette(
    "opsdroid/connector/teams/tests/test_ping_pong.yaml",
    record_mode="new_episodes",
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

    opsdroid.register_skill(test_skill, config={"name": "test"})

    with mock.patch("uuid.uuid4") as mock_uuid:
        mock_uuid.return_value = "d6d49420-f39b-4df7-a1ac-d59a935871db"
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
