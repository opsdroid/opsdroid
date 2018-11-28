import unittest
import asyncio

import asynctest
import asynctest.mock as amock

from opsdroid.__main__ import configure_lang
from opsdroid.core import OpsDroid
from opsdroid.connector.facebook import ConnectorFacebook
from opsdroid.message import Message
from opsdroid.__main__ import configure_lang


class TestConnectorFacebook(unittest.TestCase):
    """Test the opsdroid Facebook connector class."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        configure_lang({})

    def test_init(self):
        opsdroid = amock.CoroutineMock()
        connector = ConnectorFacebook({}, opsdroid=opsdroid)
        self.assertEqual(None, connector.default_room)
        self.assertEqual("facebook", connector.name)

    def test_property(self):
        opsdroid = amock.CoroutineMock()
        connector = ConnectorFacebook({}, opsdroid=opsdroid)
        self.assertEqual("facebook", connector.name)


class TestConnectorFacebookAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid Facebook connector class."""

    async def setUp(self):
        configure_lang({})

    async def test_connect(self):
        """Test the connect method adds the handlers."""
        opsdroid = amock.CoroutineMock()
        connector = ConnectorFacebook({}, opsdroid=opsdroid)
        opsdroid.web_server = amock.CoroutineMock()
        opsdroid.web_server.web_app = amock.CoroutineMock()
        opsdroid.web_server.web_app.router = amock.CoroutineMock()
        opsdroid.web_server.web_app.router.add_get = amock.CoroutineMock()
        opsdroid.web_server.web_app.router.add_post = amock.CoroutineMock()

        await connector.connect()

        self.assertTrue(opsdroid.web_server.web_app.router.add_get.called)
        self.assertTrue(opsdroid.web_server.web_app.router.add_post.called)

    async def test_facebook_message_handler(self):
        """Test the new facebook message handler."""
        import aiohttp
        opsdroid = amock.CoroutineMock()
        connector = ConnectorFacebook({}, opsdroid=opsdroid)
        req_ob = {
            "object": "page",
            "entry": [{
                "messaging": [{
                    "message": {"text": "Hello"},
                    "sender": {"id": '1234567890'}
                }]
            }]
        }
        mock_request = amock.CoroutineMock()
        mock_request.json = amock.CoroutineMock()
        mock_request.json.return_value = req_ob

        with OpsDroid() as opsdroid:
            connector.opsdroid = opsdroid
            connector.opsdroid.parse = amock.CoroutineMock()

            response = await connector.facebook_message_handler(mock_request)
            self.assertTrue(connector.opsdroid.parse.called)
            self.assertEqual(type(response), aiohttp.web.Response)
            self.assertEqual(response.status, 200)

    async def test_facebook_message_handler_invalid(self):
        """Test the new facebook message handler for invalid message."""
        import aiohttp
        opsdroid = amock.CoroutineMock()
        connector = ConnectorFacebook({}, opsdroid=opsdroid)
        req_ob = {
            "object": "page",
            "entry": [{
                "messaging": [{
                    "message": {"text": "Hello"},
                    "sender": {}
                }]
            }]
        }
        mock_request = amock.CoroutineMock()
        mock_request.json = amock.CoroutineMock()
        mock_request.json.return_value = req_ob

        with OpsDroid() as opsdroid:
            connector.opsdroid = opsdroid
            connector.opsdroid.parse = amock.CoroutineMock()

            response = await connector.facebook_message_handler(mock_request)
            self.assertFalse(connector.opsdroid.parse.called)
            self.assertLogs('_LOGGER', 'error')
            self.assertEqual(type(response), aiohttp.web.Response)
            self.assertEqual(response.status, 200)

    async def test_facebook_challenge_handler(self):
        """Test the facebook challenge handler."""
        import aiohttp
        opsdroid = amock.CoroutineMock()
        connector = ConnectorFacebook({'verify-token': 'token_123'}, opsdroid=opsdroid)
        mock_request = amock.Mock()
        mock_request.query = {
            "hub.verify_token": 'token_123',
            'hub.challenge': 'challenge_123'
        }

        response = await connector.facebook_challenge_handler(mock_request)
        self.assertEqual(type(response), aiohttp.web.Response)
        self.assertEqual(response.text, 'challenge_123')
        self.assertEqual(response.status, 200)

        mock_request.query = {
            "hub.verify_token": 'token_abc',
            'hub.challenge': 'challenge_123'
        }
        response = await connector.facebook_challenge_handler(mock_request)
        self.assertEqual(type(response), aiohttp.web.Response)
        self.assertEqual(response.status, 403)

    async def test_listen(self):
        """Test that listen does nothing."""
        opsdroid = amock.CoroutineMock()
        connector = ConnectorFacebook({}, opsdroid=opsdroid)
        await connector.listen(None)

    async def test_respond(self):
        """Test that responding sends a message."""
        post_response = amock.Mock()
        post_response.status = 200

        with OpsDroid() as opsdroid, \
                amock.patch('aiohttp.ClientSession.post',
                            new=asynctest.CoroutineMock()) as patched_request:
            self.assertTrue(opsdroid.__class__.instances)
            connector = ConnectorFacebook({}, opsdroid=opsdroid)
            room = "a146f52c-548a-11e8-a7d1-28cfe949e12d"
            test_message = Message(text="Hello world",
                                   user="Alice",
                                   room=room,
                                   connector=connector)
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(post_response)
            await test_message.respond("Response")
            self.assertTrue(patched_request.called)

    async def test_respond_bad_response(self):
        """Test that responding sends a message and get bad response."""
        post_response = amock.Mock()
        post_response.status = 401
        post_response.text = amock.CoroutineMock()
        post_response.text.return_value = "Error"

        with OpsDroid() as opsdroid, \
                amock.patch('aiohttp.ClientSession.post',
                            new=asynctest.CoroutineMock()) as patched_request:
            self.assertTrue(opsdroid.__class__.instances)
            connector = ConnectorFacebook({}, opsdroid=opsdroid)
            room = "a146f52c-548a-11e8-a7d1-28cfe949e12d"
            test_message = Message(text="Hello world",
                                   user="Alice",
                                   room=room,
                                   connector=connector)
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(post_response)
            await test_message.respond("Response")
            self.assertTrue(patched_request.called)
            self.assertTrue(post_response.text.called)
