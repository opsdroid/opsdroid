import unittest
import asyncio

import asynctest

from opsdroid.connector.slack import ConnectorSlack


class TestConnectorSlack(unittest.TestCase):
    """Test the opsdroid Slack connector class."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()

    def test_init(self):
        connector = ConnectorSlack({"api-token": "abc123"})
        self.assertEqual("#general", connector.default_room)
        self.assertEqual("slack", connector.name)

    def test_property(self):
        connector = ConnectorSlack({"api-token": "abc123"})
        self.assertEqual("slack", connector.name)

    # def test_connect(self):
    #     connector = ConnectorSlack({})
    #     with self.assertRaises(NotImplementedError):
    #         self.loop.run_until_complete(connector.connect({}))

    # def test_listen(self):
    #     connector = ConnectorSlack({})
    #     with self.assertRaises(NotImplementedError):
    #         self.loop.run_until_complete(connector.listen({}))

    # def test_respond(self):
    #     connector = ConnectorSlack({})
    #     with self.assertRaises(NotImplementedError):
    #         self.loop.run_until_complete(connector.respond({}))

    # def test_react(self):
    #     connector = ConnectorSlack({})
    #     reacted = self.loop.run_until_complete(connector.react({}, 'emoji'))
    #     self.assertFalse(reacted)

    # def test_user_typing(self):
    #     opsdroid = 'opsdroid'
    #     connector = ConnectorSlack({})
    #     user_typing = self.loop.run_until_complete(
    #         connector.user_typing(opsdroid, trigger=True))
    #     assert user_typing is None


class TestConnectorAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid Slack connector class."""

    async def test_lookup_username(self):
        connector = ConnectorSlack({"api-token": "abc123"})
        self.assertEqual("slack", connector.name)

    # async def test_disconnect(self):
    #     connector = ConnectorSlack({})
    #     res = await connector.disconnect(None)
    #     assert res is None
