from pathlib import Path

import pytest


def get_path(file_name: str) -> str:
    """Returns current path for the requested file_name"""

    return Path(__file__).parent / "responses" / file_name


@pytest.fixture
async def connector(opsdroid, mock_api_obj):
    """Initiate a basic connector setup for testing on"""

    opsdroid.config["connectors"] = {"slack": {"token": "abc123"}}
    await opsdroid.load()
    slack_connector = opsdroid.get_connector("slack")
    slack_connector.slack_web_client.base_url = mock_api_obj.base_url

    yield slack_connector
