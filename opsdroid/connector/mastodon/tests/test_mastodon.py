import pytest

import logging

from opsdroid.connector.mastodon import ConnectorMastodon, Toot
from opsdroid.events import Message, Image
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
async def test_message_sent(opsdroid, caplog):
    caplog.set_level(logging.INFO)
    mock_api = ExternalAPIMockServer()
    mock_api.add_response("/api/v1/statuses", "POST", None, 202)

    connector = ConnectorMastodon(
        {"access-token": "abc123", "api-base-url": mock_api.base_url}, opsdroid=opsdroid
    )
    await connector.connect()

    async with mock_api.running():
        await connector.send(Message(text="Hello world!"))
        assert mock_api.called("/api/v1/statuses")


@pytest.mark.asyncio
async def test_image_sent(opsdroid, caplog):
    caplog.set_level(logging.INFO)
    mock_api = ExternalAPIMockServer()
    mock_api.add_response(
        "/api/v1/media",
        "POST",
        {"id": "22348641"},
        202,
    )
    mock_api.add_response("/api/v1/statuses", "POST", None, 202)

    connector = ConnectorMastodon(
        {"access-token": "abc123", "api-base-url": mock_api.base_url}, opsdroid=opsdroid
    )
    await connector.connect()

    gif_bytes = (
        b"GIF89a\x01\x00\x01\x00\x00\xff\x00,"
        b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;"
    )
    image = Image(gif_bytes)

    async with mock_api.running():
        await connector.send(image)
        assert mock_api.called("/api/v1/media")
        assert mock_api.called("/api/v1/statuses")


@pytest.mark.asyncio
async def test_toot_sent(opsdroid, caplog):
    caplog.set_level(logging.INFO)
    mock_api = ExternalAPIMockServer()
    mock_api.add_response(
        "/api/v1/media",
        "POST",
        {"id": "22348641"},
        202,
    )
    mock_api.add_response("/api/v1/statuses", "POST", None, 202)

    connector = ConnectorMastodon(
        {"access-token": "abc123", "api-base-url": mock_api.base_url}, opsdroid=opsdroid
    )
    await connector.connect()

    gif_bytes = (
        b"GIF89a\x01\x00\x01\x00\x00\xff\x00,"
        b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;"
    )
    image = Image(gif_bytes)
    toot = Toot("My image", [image])

    async with mock_api.running():
        await connector.send(toot)
        assert mock_api.called("/api/v1/media")
        assert mock_api.called("/api/v1/statuses")
