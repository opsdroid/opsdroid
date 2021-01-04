"""Tests for the RocketChat class."""

import asyncio
import json
import unittest
import asynctest
import asynctest.mock as amock


from opsdroid.cli.start import configure_lang
from opsdroid.core import OpsDroid
from opsdroid.connector.gitter import ConnectorGitter
from opsdroid.events import Message


class TestConnectorGitter(unittest.TestCase):
    """Test the opsdroid github connector class."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()

    def test_init(self):
        """Test that the connector is initialised properly."""
        connector = ConnectorGitter(
            {"bot-name": "github", "room-id": "test-id", "token": "test-token"}
        )
        self.assertEqual("gitter", connector.name)


class TestConnectorGitterAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid github connector class."""

    def setUp(self):
        opsdroid = amock.CoroutineMock()
        configure_lang({})
        self.connector = ConnectorGitter(
            {"bot-name": "github", "room-id": "test-id", "token": "test-token"},
            opsdroid=opsdroid,
        )
        with amock.patch("aiohttp.ClientSession") as mocked_session:
            self.connector.session = mocked_session

    async def test_connect(self):
        BOT_GITTER_ID = "12345"
        with amock.patch("aiohttp.ClientSession.get") as patched_request:
            mockresponse = amock.CoroutineMock()
            mockresponse.status = 200
            mockresponse.json = amock.CoroutineMock(return_value={"login": "opsdroid", "id": BOT_GITTER_ID})
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(mockresponse)
            await self.connector.connect()
        assert self.connector.bot_gitter_id == BOT_GITTER_ID

    def test_build_url(self):
        self.assertEqual(
            "test/api/test-id/chatMessages?access_token=token",
            self.connector.build_url(
                "test/api", "test-id", "chatMessages", access_token="token"
            ),
        )

    async def test_parse_message(self):
        await self.connector.parse_message(
            b'{"text":"hello", "fromUser":{"username":"testUSer"}}'
        )

    async def test_parse_message_key_error(self):
        await self.connector.parse_message(b'{"text":"hello"}')
        self.assertLogs("_LOGGER", level="ERROR")

    async def test_listen_loop(self):
        """Test that listening consumes from the socket."""
        connector = ConnectorGitter(
            {"bot-name": "github", "room-id": "test-id", "token": "test-token"},
            opsdroid=OpsDroid(),
        )
        connector._get_messages = amock.CoroutineMock()
        connector._get_messages.side_effect = Exception()
        with self.assertRaises(Exception):
            await connector.listen()
        self.assertTrue(connector._get_messages.called)

    async def test_listen_break_loop(self):
        """Test that listening consumes from the socket."""
        connector = connector = ConnectorGitter(
            {"bot-name": "github", "room-id": "test-id", "token": "test-token"},
            opsdroid=OpsDroid(),
        )
        connector._get_messages = amock.CoroutineMock()
        connector._get_messages.side_effect = AttributeError
        await connector.listen()
        self.assertTrue(connector._get_messages.called)

    async def test_get_message(self):
        """Test that listening consumes from the socket."""

        BOT_GITTER_ID = "12345"
        OTHER_GITTER_ID = "67890"
        async def iter_chuncked1(n=None):
            response = [
                {"text": "hi", "fromUser": {"username": "not a bot", "id": OTHER_GITTER_ID}},
                {"text": "hi", "fromUser": {"username": "bot", "id": BOT_GITTER_ID}},
                {"text": "hi", "fromUser": {"username": "not a bot", "id": OTHER_GITTER_ID}},
            ]
            for doc in response:
                yield json.dumps(doc).encode()

        response1 = amock.CoroutineMock()
        response1.content.iter_chunked = iter_chuncked1

        connector = ConnectorGitter(
            {"bot-name": "github", "room-id": "test-id", "token": "test-token"},
            opsdroid=OpsDroid(),
        )
        # Connect first, in order to set bot_gitter_id.
        with amock.patch("aiohttp.ClientSession.get") as patched_request:
            mockresponse = amock.CoroutineMock()
            mockresponse.status = 200
            mockresponse.json = amock.CoroutineMock(return_value={"login": "opsdroid", "id": BOT_GITTER_ID})
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(mockresponse)
            await connector.connect()

        connector.opsdroid.parse = amock.CoroutineMock()
        connector.response = response1
        assert await connector._get_messages() is None
        # Should be called *twice* given these three messages (skipping own message)
        assert connector.opsdroid.parse.call_count == 2

    async def test_send_message_success(self):
        post_response = amock.Mock()
        post_response.status = 200

        with OpsDroid(), amock.patch.object(
            self.connector.session, "post"
        ) as patched_request:
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(post_response)
            await self.connector.send_message(Message("", "", "", self.connector))

    async def test_send_message_not_success(self):
        post_response = amock.Mock()
        post_response.status = 400

        with OpsDroid(), amock.patch.object(
            self.connector.session, "post"
        ) as patched_request:
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(post_response)
            await self.connector.send_message(Message("", "", "", self.connector))

    async def test_disconnect(self):
        post_response = amock.Mock()
        with OpsDroid(), amock.patch.object(
            self.connector.session, "close"
        ) as patched_request:
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(post_response)
            await self.connector.disconnect()
