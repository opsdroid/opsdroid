"""Tests for the ConnectorSlack class."""
import asyncio

import unittest
import unittest.mock as mock
import asynctest
import asynctest.mock as amock
from ciscosparkapi import CiscoSparkAPI

from opsdroid.core import OpsDroid
from opsdroid.connector.ciscospark import ConnectorCiscoSpark
from opsdroid.events import Message, Reaction
from opsdroid.__main__ import configure_lang


class TestConnectorCiscoSpark(unittest.TestCase):
    """Test the opsdroid CiscoSpark connector class."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        configure_lang({})

    def test_init(self):
        """Test that the connector is initialised properly."""
        connector = ConnectorCiscoSpark({})
        self.assertEqual("ciscospark", connector.name)
        self.assertEqual("opsdroid", connector.bot_name)

    def test_missing_api_key(self):
        """Test that creating without an API without config raises an error."""
        with self.assertRaises(TypeError):
            ConnectorCiscoSpark()

class TestConnectorCiscoSparkAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid Cisco Spark connector class."""

    async def setUp(self):
        configure_lang({})

    async def test_connect(self):
        connector = ConnectorCiscoSpark({"access-token": "abc123"})

        opsdroid = amock.CoroutineMock()
        opsdroid.eventloop = self.loop
        connector.clean_up_webhooks = amock.CoroutineMock()
        connector.subscribe_to_rooms = amock.CoroutineMock()
        connector.set_own_id = amock.CoroutineMock()

        with amock.patch(
            "websockets.connect", new=amock.CoroutineMock()
        ) as mocked_websocket_connect:
            await connector.connect(opsdroid=OpsDroid())

        self.assertTrue(connector.clean_up_webhooks.called)
        self.assertTrue(connector.subscribe_to_rooms.called)
        self.assertTrue(connector.set_own_id.called)
