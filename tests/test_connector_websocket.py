import unittest
import asyncio

import asynctest

from opsdroid.connector.websocket import ConnectorWebsocket


class TestConnectorWebsocket(unittest.TestCase):
    """Test the opsdroid Websocket connector class."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()

    def test_init(self):
        connector = ConnectorWebsocket({})
        self.assertEqual(None, connector.default_room)
        self.assertEqual("websocket", connector.name)

    def test_property(self):
        connector = ConnectorWebsocket({})
        self.assertEqual("websocket", connector.name)

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
    """Test the async methods of the opsdroid Websocket connector class."""

    async def test_lookup_username(self):
        connector = ConnectorWebsocket({})

    # async def test_disconnect(self):
    #     connector = ConnectorSlack({})
    #     res = await connector.disconnect(None)
    #     assert res is None
