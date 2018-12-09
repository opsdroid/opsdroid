"""Tests for the ConnectorMatrix class."""
import asyncio

import unittest
import unittest.mock as mock
import asynctest
import asynctest.mock as amock

from opsdroid.connector.matrix import ConnectorMatrix
from opsdroid.message import Message
from opsdroid.__main__ import configure_lang


class TestConnectorMatrix(unittest.TestCase):
    """Test the opsdroid Matrix connector class."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        configure_lang({})

    def test_init(self):
        """Test that the connector is initialised properly."""
        connector = ConnectorMatrix(
            {"room": "#notaroom:matrix.org",
             "mxid": "@nobody:matrix.org",
             "password": "nothing"}
        )
        self.assertEqual("#notaroom:matrix.org", connector.default_room)
        self.assertEqual("ConnectorMatrix", connector.name)

    def test_missing_api_key(self):
        """Test that creating without an API key raises an error."""
        with self.assertRaises(KeyError):
            ConnectorMatrix({})

    # def test_listen(self):
    #     connector = ConnectorMatrix({})
    #     with self.assertRaises(NotImplementedError):
    #         self.loop.run_until_complete(connector.listen({}))

    # def test_respond(self):
    #     connector = ConnectorMatrix({})
    #     with self.assertRaises(NotImplementedError):
    #         self.loop.run_until_complete(connector.respond({}))

    # def test_react(self):
    #     connector = ConnectorMatrix({})
    #     reacted = self.loop.run_until_complete(connector.react({}, 'emoji'))
    #     self.assertFalse(reacted)

    # def test_user_typing(self):
    #     opsdroid = 'opsdroid'
    #     connector = ConnectorMatrix({})
    #     user_typing = self.loop.run_until_complete(
    #         connector.user_typing(opsdroid, trigger=True))
    #     assert user_typing is None


class TestConnectorMatrixAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid Matrix connector class."""

    async def test_connect(self):
        connector = ConnectorMatrix({"api-token": "abc123"})
        opsdroid = amock.CoroutineMock()
        opsdroid.eventloop = self.loop
        connector.matrixer.rtm.start = amock.CoroutineMock()
        connector.keepalive_websocket = amock.CoroutineMock()
        with amock.patch('websockets.connect', new=amock.CoroutineMock()) \
                as mocked_websocket_connect:
            await connector.connect(opsdroid)
        self.assertTrue(connector.matrixer.rtm.start.called)
        self.assertTrue(mocked_websocket_connect.called)
        self.assertTrue(connector.keepalive_websocket.called)

    async def test_reconnect_on_error(self):
        import aiohttp
        connector = ConnectorMatrix({"api-token": "abc123"})
        connector.matrixer.rtm.start = amock.CoroutineMock()
        connector.matrixer.rtm.start.side_effect = aiohttp.ClientOSError()
        connector.reconnect = amock.CoroutineMock()

        await connector.connect()
        self.assertTrue(connector.reconnect.called)

    async def test_listen_loop(self):
        """Test that listening consumes from the socket."""
        connector = ConnectorMatrix({"api-token": "abc123"})
        connector.receive_from_websocket = amock.CoroutineMock()
        connector.receive_from_websocket.side_effect = Exception()
        with self.assertRaises(Exception):
            await connector.listen(amock.CoroutineMock())
        self.assertTrue(connector.receive_from_websocket.called)

    async def test_receive_from_websocket(self):
        """Test receive_from_websocket receives and reconnects."""
        import websockets
        connector = ConnectorMatrix({"api-token": "abc123"})

        connector.websocket = amock.CoroutineMock()
        connector.websocket.recv = amock.CoroutineMock()
        connector.websocket.recv.return_value = '[]'
        connector.process_message = amock.CoroutineMock()
        await connector.receive_from_websocket()
        self.assertTrue(connector.websocket.recv.called)
        self.assertTrue(connector.process_message.called)

        connector.websocket.recv.side_effect = \
            websockets.exceptions.ConnectionClosed(500, "Mock Error")
        connector.reconnect = amock.CoroutineMock()
        await connector.receive_from_websocket()
        self.assertTrue(connector.reconnect.called)

    async def test_process_message(self):
        """Test processing a matrix message."""
        connector = ConnectorMatrix({"api-token": "abc123"})
        connector.lookup_username = amock.CoroutineMock()
        connector.lookup_username.return_value = {"name": "testuser"}
        connector.opsdroid = amock.CoroutineMock()
        connector.opsdroid.parse = amock.CoroutineMock()

        message = {   # https://api.matrix.com/events/message
            "type": "message",
            "channel": "C2147483705",
            "user": "U2147483697",
            "text": "Hello, world!",
            "ts": "1355517523.000005",
            "edited": {
                "user": "U2147483697",
                "ts": "1355517536.000001"
            }
        }
        await connector.process_message(message)
        self.assertTrue(connector.opsdroid.parse.called)

        connector.opsdroid.parse.reset_mock()
        message["subtype"] = "bot_message"
        await connector.process_message(message)
        self.assertFalse(connector.opsdroid.parse.called)
        del message["subtype"]

        connector.opsdroid.parse.reset_mock()
        connector.lookup_username.side_effect = ValueError
        await connector.process_message(message)
        self.assertFalse(connector.opsdroid.parse.called)

    async def test_keepalive_websocket_loop(self):
        """Test that listening consumes from the socket."""
        connector = ConnectorMatrix({"api-token": "abc123"})
        connector.ping_websocket = amock.CoroutineMock()
        connector.ping_websocket.side_effect = Exception()
        with self.assertRaises(Exception):
            await connector.keepalive_websocket()
        self.assertTrue(connector.ping_websocket.called)

    async def test_ping_websocket(self):
        """Test pinging the websocket."""
        import websockets
        connector = ConnectorMatrix({"api-token": "abc123"})
        with amock.patch('asyncio.sleep', new=amock.CoroutineMock()) \
                as mocked_sleep:
            connector.websocket = amock.CoroutineMock()
            connector.websocket.send = amock.CoroutineMock()
            await connector.ping_websocket()
            self.assertTrue(mocked_sleep.called)
            self.assertTrue(connector.websocket.send.called)

            connector.reconnect = amock.CoroutineMock()
            connector.websocket.send.side_effect = \
                websockets.exceptions.ConnectionClosed(500, "Mock Error")
            await connector.ping_websocket()
            self.assertTrue(connector.reconnect.called)

    async def test_lookup_username(self):
        """Test that looking up a username works and that it caches."""
        connector = ConnectorMatrix({"api-token": "abc123"})
        connector.matrixer.users.info = amock.CoroutineMock()
        mock_user = mock.Mock()
        mock_user.body = {"user": {"name": "testuser"}}
        connector.matrixer.users.info.return_value = mock_user

        self.assertEqual(len(connector.known_users), 0)

        await connector.lookup_username('testuser')
        self.assertTrue(len(connector.known_users), 1)
        self.assertTrue(connector.matrixer.users.info.called)

        connector.matrixer.users.info.reset_mock()
        await connector.lookup_username('testuser')
        self.assertEqual(len(connector.known_users), 1)
        self.assertFalse(connector.matrixer.users.info.called)

        with self.assertRaises(ValueError):
            mock_user.body = {"user": None}
            connector.matrixer.users.info.return_value = mock_user
            await connector.lookup_username('invaliduser')

    async def test_respond(self):
        connector = ConnectorMatrix({"api-token": "abc123"})
        connector.matrixer.chat.post_message = amock.CoroutineMock()
        await connector.respond(Message("test", "user", "room", connector))
        self.assertTrue(connector.matrixer.chat.post_message.called)

    async def test_reconnect(self):
        connector = ConnectorMatrix({"api-token": "abc123"})
        connector.connect = amock.CoroutineMock()
        with amock.patch('asyncio.sleep') as mocked_sleep:
            await connector.reconnect(10)
            self.assertTrue(connector.connect.called)
            self.assertTrue(mocked_sleep.called)

    async def test_replace_usernames(self):
        connector = ConnectorMatrix({"api-token": "abc123"})
        connector.lookup_username = amock.CoroutineMock()
        connector.lookup_username.return_value = {"name": 'user'}
        result = await connector.replace_usernames("Hello <@U023BECGF>!")
        self.assertEqual(result, "Hello user!")
