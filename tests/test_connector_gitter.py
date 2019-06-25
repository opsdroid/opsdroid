"""Tests for the RocketChat class."""

import os.path

import asyncio
import unittest
import unittest.mock as mock
import asynctest
import asynctest.mock as amock

from opsdroid.__main__ import configure_lang
from opsdroid.core import OpsDroid
from opsdroid.connector.gitter import ConnectorGitter
from opsdroid.events import Message


class TestConnectorGitter(unittest.TestCase):
    """Test the opsdroid github connector class."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()

    def test_init(self):
        """Test that the connector is initialised properly."""
        connector = ConnectorGitter({"bot-name": "github", "room-id": "test-id", "access-token":"test-token"})
        self.assertEqual("gitter", connector.name)


class TestConnectorGitHubAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid github connector class."""

    def setUp(self):
        opsdroid = amock.CoroutineMock()
        configure_lang({})
        self.connector = ConnectorGitter(
            {"bot-name": "github", "room-id": "test-id", "access-token":"test-token"}, opsdroid=opsdroid
        )

    async def test_connect(self):
        with amock.patch("aiohttp.ClientSession.get") as patched_request:
            mockresponse = amock.CoroutineMock()
            mockresponse.status = 200
            mockresponse.json = amock.CoroutineMock(return_value={"login": "opsdroid"})
            await self.connector.connect()

    def test_build_url(self):
        self.assertEqua("test/api/test-id/chatMessage/token",self.connector.build_url("test/api", "test-id", "chatMessages", access_token= "token"))

    async def test_disconnect(self):
        self.assertEqual(await self.connector.disconnect(), None)



