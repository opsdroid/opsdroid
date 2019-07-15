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
        with amock.patch("aiohttp.ClientSession") as mocked_session:
            self.connector.session = mocked_session

    async def test_connect(self):
        with amock.patch("aiohttp.ClientSession.get") as patched_request:
            mockresponse = amock.CoroutineMock()
            mockresponse.status = 200
            mockresponse.json = amock.CoroutineMock(return_value={"login": "opsdroid"})
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(mockresponse)
            await self.connector.connect()

    def test_build_url(self):
        self.assertEqual("test/api/test-id/chatMessages?access_token=token",self.connector.build_url("test/api", "test-id", "chatMessages", access_token= "token"))


    async def test_parse_message(self):
        self.connector.parse_message("{'text':'hello', 'fromUser':{'username':'testUSer'}}")

    async def test_listen_loop(self):
        """Test that listening consumes from the socket."""
        connector = ConnectorGitter(
            {"bot-name": "github", "room-id": "test-id", "access-token": "test-token"}, opsdroid=OpsDroid()
        )
        connector._get_messages = amock.CoroutineMock()
        connector._get_messages.side_effect = Exception()
        with self.assertRaises(Exception):
            await connector.listen()
        self.assertTrue(connector._get_messages.called)


    async def test_get_message(self):
        """Test that listening consumes from the socket."""

        self.connector.parse_message  = amock.CoroutineMock()
        self.connector.opsdroid.parse = amock.CoroutineMock()
        parse_message = amock.patch("opsdroid.connector.gitter.ConnectorGitter.parse_message")
        patch_iter                   =  amock.patch("aiohttp.ClientSession.get")
        patch_iter.return_value      =  bytes("[{'message':'hi'},{'message':'hi'}]", 'utf-8')
        parse_message.return_value   =   "hi"
        self.connector._get_messages()
        self.assertTrue(self.connector.parse_message.called)
        self.assertTrue(self.connector.opsdroid.parse.called)


    async def test_send_message_success(self):
        post_response = amock.Mock()
        post_response.status = 200

        with OpsDroid() as opsdroid, amock.patch.object(
                self.connector.session, "post"
        ) as patched_request:
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(post_response)
            await self.connector.send_message(Message("","","",self.connector))

    async def test_send_message_not_success(self):
        post_response = amock.Mock()
        post_response.status = 400

        with OpsDroid() as opsdroid, amock.patch.object(
                self.connector.session, "post"
        ) as patched_request:
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(post_response)
            await self.connector.send_message(Message("","","",self.connector))


    async def test_disconnect(self):
        post_response = amock.Mock()
        with OpsDroid() as opsdroid, amock.patch.object(
                self.connector.session, "close"
        ) as patched_request:
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(post_response)
            await self.connector.disconnect()








