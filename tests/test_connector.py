import unittest
import asyncio

import asynctest

from opsdroid.connector import Connector


class TestConnectorBaseClass(unittest.TestCase):
    """Test the opsdroid connector base class."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()

    def test_init(self):
        config = {"example_item": "test"}
        connector = Connector(config)
        self.assertEqual(None, connector.default_room)
        self.assertEqual("", connector.name)
        self.assertEqual("test", connector.config["example_item"])

    def test_property(self):
        connector = Connector({"name": "shell"})
        self.assertEqual("shell", connector.configuration.get("name"))

    def test_connect(self):
        connector = Connector({})
        with self.assertRaises(NotImplementedError):
            self.loop.run_until_complete(connector.connect({}))

    def test_listen(self):
        connector = Connector({})
        with self.assertRaises(NotImplementedError):
            self.loop.run_until_complete(connector.listen({}))

    def test_respond(self):
        connector = Connector({})
        with self.assertRaises(NotImplementedError):
            self.loop.run_until_complete(connector.respond({}))

    def test_user_typing(self):
        opsdroid = 'opsdroid'
        connector = Connector({})
        user_typing = self.loop.run_until_complete(
            connector.user_typing(opsdroid, trigger=True))
        assert user_typing is None


class TestConnectorAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid connector base class."""

    async def test_disconnect(self):
        connector = Connector({})
        res = await connector.disconnect(None)
        assert res is None
