"""Tests for the Connector Webex Teams class."""
import asyncio

import unittest
from unittest import TestCase
from unittest.mock import AsyncMock, Mock, patch

from opsdroid.core import OpsDroid
from opsdroid.connector.webexteams import ConnectorWebexTeams
from opsdroid.events import Message
from opsdroid.cli.start import configure_lang


class TestConnectorCiscoWebexTeams(unittest.TestCase):
    """Test the opsdroid Webex Teams connector class."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        configure_lang({})

    def test_init(self):
        """Test that the connector is initialised properly."""
        connector = ConnectorWebexTeams({})
        self.assertEqual("webexteams", connector.name)
        self.assertEqual("opsdroid", connector.bot_name)

    def test_webhook_url_is_valid(self):
        connector = ConnectorWebexTeams({"webhook-url": "https://example.com"})
        assert connector.config.get("webhook-url").startswith("https")

    def test_missing_api_key(self):
        """Test that creating without an API without config raises an error."""
        with self.assertRaises(TypeError):
            ConnectorWebexTeams()


class TestConnectorCiscoSparkAsync(TestCase):
    """Test the async methods of the opsdroid webex teams connector class."""

    async def setUp(self):
        configure_lang({})

    async def test_connect(self):
        connector = ConnectorWebexTeams({"token": "abc123"}, opsdroid=OpsDroid())

        opsdroid = AsyncMock()
        opsdroid.eventloop = self.loop
        connector.clean_up_webhooks = AsyncMock()
        connector.subscribe_to_rooms = AsyncMock()
        connector.set_own_id = AsyncMock()

        with patch("websockets.connect", new=AsyncMock()):
            await connector.connect()

        self.assertTrue(connector.clean_up_webhooks.called)
        self.assertTrue(connector.subscribe_to_rooms.called)
        self.assertTrue(connector.set_own_id.called)

    async def test_message_handler(self):
        connector = ConnectorWebexTeams({"token": "abc123"})
        connector.opsdroid = OpsDroid()
        connector.bot_spark_id = "spark123"
        connector.api = AsyncMock()
        request = Mock()
        request.json = AsyncMock()
        request.json.return_value = {
            "data": {"id": "3vABZrQgDzfcz7LZi", "personId": "21ABZrQgDzfcz7Lsi"}
        }
        message = Mock()
        connector.api.messages.get = Mock()
        message.text = "Hello"
        message.roomId = "90ABCrWgrzfcz7LZi"
        message.roomType = "general"
        connector.api.messages.get.return_value = message
        connector.get_person = AsyncMock()
        person = AsyncMock()
        person.displayName = "Himanshu"
        connector.get_person.return_value = person

        response = await connector.webexteams_message_handler(request)
        self.assertLogs("_LOGGER", "debug")
        self.assertEqual(201, response.status)
        self.assertEqual('"Received"', response.text)
        self.assertTrue(connector.api.messages.get.called)
        self.assertTrue(connector.get_person.called)

        connector.opsdroid = AsyncMock()
        connector.opsdroid.parse = AsyncMock()
        connector.opsdroid.parse.side_effect = KeyError
        await connector.webexteams_message_handler(request)
        self.assertLogs("_LOGGER", "error")

    async def test_connect_fail_keyerror(self):
        connector = ConnectorWebexTeams({}, opsdroid=OpsDroid())
        connector.clean_up_webhooks = AsyncMock()
        connector.subscribe_to_rooms = AsyncMock()
        connector.set_own_id = AsyncMock()
        await connector.connect()
        self.assertLogs("_LOGGER", "error")

    async def test_listen(self):
        """Test the listen method.

        The Webex Teams connector listens using an API endoint and so the listen
        method should just pass and do nothing. We just need to test that it
        does not block.

        """
        connector = ConnectorWebexTeams({}, opsdroid=OpsDroid())
        self.assertEqual(await connector.listen(), None)

    async def test_respond(self):
        connector = ConnectorWebexTeams({"token": "abc123"})
        connector.api = AsyncMock()
        connector.api.messages.create = AsyncMock()
        message = Message(
            text="Hello",
            user="opsdroid",
            target={"id": "3vABZrQgDzfcz7LZi"},
            connector=None,
        )
        await connector.send(message)
        self.assertTrue(connector.api.messages.create.called)

    async def test_get_person(self):
        connector = ConnectorWebexTeams({"token": "abc123"})
        connector.api = AsyncMock()
        connector.api.messages.create = AsyncMock()
        connector.api.people.get = AsyncMock()
        connector.api.people.get.return_value = "Himanshu"
        self.assertEqual(len(connector.people), 0)
        await connector.get_person("3vABZrQgDzfcz7LZi")
        self.assertEqual(len(connector.people), 1)

    async def test_subscribe_to_rooms(self):
        connector = ConnectorWebexTeams(
            {"token": "abc123", "webhook-url": "http://127.0.0.1"}
        )
        connector.api = AsyncMock()
        connector.opsdroid = AsyncMock()
        connector.opsdroid.web_server.web_app.router.add_post = AsyncMock()
        connector.api.webhooks.create = AsyncMock()
        await connector.subscribe_to_rooms()
        self.assertTrue(connector.api.webhooks.create.called)
        self.assertTrue(connector.opsdroid.web_server.web_app.router.add_post.called)

    async def test_clean_up_webhooks(self):
        connector = ConnectorWebexTeams({"token": "abc123"})
        connector.api = AsyncMock()
        x = AsyncMock()
        x.id = AsyncMock()
        connector.api.webhooks.list = Mock()
        connector.api.webhooks.list.return_value = [x, x]
        connector.api.webhooks.delete = Mock()
        await connector.clean_up_webhooks()
        self.assertTrue(connector.api.webhooks.list.called)
        self.assertTrue(connector.api.webhooks.delete.called)

    async def test_set_own_id(self):
        connector = ConnectorWebexTeams({"token": "abc123"})
        connector.api = AsyncMock()
        connector.api.people.me().id = "3vABZrQgDzfcz7LZi"
        await connector.set_own_id()
        self.assertTrue(connector.bot_webex_id, "3vABZrQgDzfcz7LZi")
