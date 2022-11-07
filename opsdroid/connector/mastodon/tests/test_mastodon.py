import pytest

import logging

from opsdroid.connector.mastodon import ConnectorMastodon
from opsdroid.events import Message
from opsdroid.testing import ExternalAPIMockServer


@pytest.fixture
async def connector(opsdroid, mock_api_obj):
    opsdroid.config["connectors"] = {
        "mastodon": {"access-token": "abc123", "api-base-url": "https://example.com"}
    }

    await opsdroid.load()
    return opsdroid.get_connector("mastodon")


def test_init(opsdroid):
    connector = ConnectorMastodon({}, opsdroid=opsdroid)
    assert connector.name == "mastodon"
    assert connector.opsdroid == opsdroid


@pytest.mark.asyncio
async def test_toot_sent(opsdroid, caplog):
    caplog.set_level(logging.INFO)
    mock_api = ExternalAPIMockServer()
    mock_api.add_response("/api/v1/statuses", "POST", None, 202)

    opsdroid.config["connectors"] = {
        "mastodon": {"access-token": "abc123", "api-base-url": mock_api.base_url}
    }
    await opsdroid.load()
    connector = opsdroid.get_connector("mastodon")
    await connector.connect()

    async with mock_api.running():
        await connector.send(Message(text="Hello world!"))
        assert mock_api.called("/api/v1/statuses")
