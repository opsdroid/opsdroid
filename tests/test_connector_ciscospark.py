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

    async def test_connect_fail_keyerror(self):
        connector = ConnectorCiscoSpark({})
        connector.clean_up_webhooks = amock.CoroutineMock()
        connector.subscribe_to_rooms = amock.CoroutineMock()
        connector.set_own_id = amock.CoroutineMock()
        await connector.connect(opsdroid=OpsDroid())
        self.assertLogs("_LOGGER", "error")

    async def test_respond(self):
        connector = ConnectorCiscoSpark({"access-token": "abc123"})
        connector.api = amock.CoroutineMock()
        connector.api.messages.create = amock.CoroutineMock()
        message = amock.CoroutineMock()
        message.room.return_value = {"id": "3vABZrQgDzfcz7LZi"}
        message.text.return_value = "Hello"
        await connector.respond(message)
        self.assertTrue(connector.api.messages.create.called)

    async def test_get_person(self):
        connector = ConnectorCiscoSpark({"access-token": "abc123"})
        connector.api = amock.CoroutineMock()
        connector.api.messages.create = amock.CoroutineMock()
        connector.api.people.get = amock.CoroutineMock()
        connector.api.people.get.return_value = "Himanshu"
        self.assertEqual(len(connector.people), 0)
        await connector.get_person("3vABZrQgDzfcz7LZi")
        self.assertEqual(len(connector.people), 1)

    async def test_subscribe_to_rooms(self):
        connector = ConnectorCiscoSpark(
            {"access-token": "abc123", "webhook-url": "http:\\127.0.0.1"}
        )
        connector.api = amock.CoroutineMock()
        connector.opsdroid = amock.CoroutineMock()
        connector.opsdroid.web_server.web_app.router.add_post = amock.CoroutineMock()
        connector.api.webhooks.create = amock.CoroutineMock()
        await connector.subscribe_to_rooms()
        self.assertTrue(connector.api.webhooks.create.called)
        self.assertTrue(connector.opsdroid.web_server.web_app.router.add_post.called)
