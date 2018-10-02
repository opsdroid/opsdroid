import unittest
import asyncio

import asynctest
import asynctest.mock as amock

from opsdroid.core import OpsDroid
from opsdroid.connector.facebook import ConnectorFacebook
from opsdroid.message import Message


class TestConnectorFacebook(unittest.TestCase):
    """Test the opsdroid Facebook connector class."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()

    def test_init(self):
        connector = ConnectorFacebook({})
        self.assertEqual(None, connector.default_room)
        self.assertEqual("facebook", connector.name)

    def test_property(self):
        connector = ConnectorFacebook({})
        self.assertEqual("facebook", connector.name)


class TestConnectorFacebookAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid Facebook connector class."""

    async def test_connect(self):
        """Test the connect method adds the handlers."""
        connector = ConnectorFacebook({})
        opsdroid = amock.CoroutineMock()
        opsdroid.web_server = amock.CoroutineMock()
        opsdroid.web_server.web_app = amock.CoroutineMock()
        opsdroid.web_server.web_app.router = amock.CoroutineMock()
        opsdroid.web_server.web_app.router.add_get = amock.CoroutineMock()
        opsdroid.web_server.web_app.router.add_post = amock.CoroutineMock()

        await connector.connect(opsdroid)

        self.assertTrue(opsdroid.web_server.web_app.router.add_get.called)
        self.assertTrue(opsdroid.web_server.web_app.router.add_post.called)

    async def test_facebook_message_handler(self):
        """Test the new facebook message handler."""
        import aiohttp
        connector = ConnectorFacebook({})
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
            self.assertEqual(response.status, 201)

    async def test_facebook_challenge_handler(self):
        """Test the facebook challenge handler."""
        import aiohttp
        connector = ConnectorFacebook({'verify-token': 'token_123'})
        mock_request = amock.Mock()
        mock_request.query = amock.Mock()
        mock_request.query.return_value = {"hub.verify_token": 'token_123', 'hub.challenge': 'challenge_123'}

        response = await connector.facebook_challenge_handler(mock_request)
        self.assertEqual(type(response), aiohttp.web.Response)
        self.assertEqual(response.text, 'challenge_123')
        self.assertEqual(response.status, 200)

        mock_request.query.return_value = {"hub.verify_token": 'token_abc', 'hub.challenge': 'challenge_123'}
        response = await connector.facebook_challenge_handler(mock_request)
        self.assertEqual(type(response), aiohttp.web.Response)
        self.assertEqual(response.status, 403)

    async def test_respond(self):
        """Test that responding sends a message."""
        with OpsDroid() as opsdroid, amock.patch('aiohttp.ClientSession',
                                                 new=asynctest.CoroutineMock()) as mock_ClientSession:
            self.assertTrue(opsdroid.__class__.instances)
            connector = ConnectorFacebook({})
            room = "a146f52c-548a-11e8-a7d1-28cfe949e12d"
            test_message = Message(text="Hello world",
                                   user="Alice",
                                   room=room,
                                   connector=connector)
            mock_ClientSession.post = amock.CoroutineMock()
            post_response = amock.CoroutineMock()
            post_response.status = 200
            post_response.text = amock.CoroutineMock()
            post_response.text.return_value = "Error"
            mock_ClientSession.post = amock.CoroutineMock()
            mock_ClientSession.post.return_value = post_response

            await test_message.respond("Response")
            self.assertTrue(mock_ClientSession.post.called)
            self.assertFalse(post_response.text.called)
