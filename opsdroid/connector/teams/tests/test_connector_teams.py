import pytest
import vcr

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


# @pytest.mark.add_response(
#     "/user", "GET", get_response_path("github_user.json"), status=200
# )
@pytest.mark.asyncio
@vcr.use_cassette(
    "opsdroid/connector/teams/tests/test_ping_pong.yaml",
    filter_post_data_parameters=["client_id", "client_secret"],
)
async def test_ping_pong(opsdroid, connector, mock_api, mock_api_obj):
    """Test a message is received and response is sent."""

    @match_regex(r"ping")
    async def test_skill(opsdroid, config, event):
        assert event.connector.name == "teams"
        assert event.text == "ping"

        await event.respond("pong")

    opsdroid.register_skill(test_skill, config={"name": "test"})

    async with running_opsdroid(opsdroid):
        with open(get_response_path("teams_ping_payload.json"), "r") as fh:
            data = fh.read()
            # data.replace("<mock_api_obj>", mock_api_obj.base_url)

            resp = await call_endpoint(
                opsdroid,
                "/connector/teams",
                "POST",
                data=data,
                headers={"Content-Type": "application/json"},
            )
            assert resp.status == 200
