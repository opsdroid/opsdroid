import unittest
import asyncio

import asynctest
import asynctest.mock as amock

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


class TestConnectorAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid Websocket connector class."""

    async def test_connect(self):
        """Test the connect method adds the handlers."""
        connector = ConnectorWebsocket({})
        opsdroid = amock.CoroutineMock()
        opsdroid.web_server = amock.CoroutineMock()
        opsdroid.web_server.web_app = amock.CoroutineMock()
        opsdroid.web_server.web_app.router = amock.CoroutineMock()
        opsdroid.web_server.web_app.router.add_get = amock.CoroutineMock()
        opsdroid.web_server.web_app.router.add_post = amock.CoroutineMock()

        await connector.connect(opsdroid)

        self.assertTrue(opsdroid.web_server.web_app.router.add_get.called)
        self.assertTrue(opsdroid.web_server.web_app.router.add_post.called)

    async def test_new_websocket_handler(self):
        """Test the new websocket handler."""
        import aiohttp.web
        connector = ConnectorWebsocket({})
        connector.max_connections = 1
        self.assertEqual(len(connector.available_connections), 0)

        response = await connector.new_websocket_handler(None)
        self.assertTrue(isinstance(response, aiohttp.web.Response))
        self.assertEqual(len(connector.available_connections), 1)
        self.assertEqual(response.status, 200)

        fail_response = await connector.new_websocket_handler(None)
        self.assertTrue(isinstance(fail_response, aiohttp.web.Response))
        self.assertEqual(fail_response.status, 429)

    async def test_lookup_username(self):
        """Test lookup up the username."""
        connector = ConnectorWebsocket({})
        self.assertEqual("websocket", connector.name)
