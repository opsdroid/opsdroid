"""Tests for the RocketChat class."""
import asyncio
import unittest
import unittest.mock as mock
import asynctest
import asynctest.mock as amock

from opsdroid.core import OpsDroid
from opsdroid.connector.rocketchat import RocketChat
from opsdroid.message import Message
from opsdroid.__main__ import configure_lang


class TestRocketChat(unittest.TestCase):
    """Test the opsdroid Slack connector class."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        configure_lang({})

    def test_init(self):
        """Test that the connector is initialised properly."""
        connector = RocketChat({
            'name': 'rocket.chat',
            'access-token': 'test',
            'user-id': 'userID'
        })
        self.assertEqual("general", connector.default_room)
        self.assertEqual("rocket.chat", connector.name)

    def test_missing_token(self):
        """Test that attempt to connect without info raises an error."""
        RocketChat({})
        self.assertLogs('_LOGGER', 'error')


class TestConnectorRocketChatAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid Slack connector class."""

    def setUp(self):
        self.connector = RocketChat({
                'name': 'rocket.chat',
                'token': 'test',
                'user-id': 'userID',
                'default_room': "test"
            })
        self.connector.latest_update = '2018-10-08T12:57:37.126Z'

    async def test_connect(self):
        connect_response = amock.Mock()
        connect_response.status = 200
        connect_response.json = amock.CoroutineMock()
        connect_response.return_value = {
            "_id": "3vABZrQgDzfcz7LZi",
            "name": "Fábio Rosado",
            "emails": [
                {
                    "address": "fabioglrosado@gmail.com",
                    "verified": True
                }
            ],
            "status": "online",
            "statusConnection": "online",
            "username": "FabioRosado",
            "utcOffset": 1,
            "active": True,
            "roles": [
                "user"
            ],
            "settings": {},
            "email": "fabioglrosado@gmail.com",
            "success": True
        }

        with OpsDroid() as opsdroid, \
            amock.patch('aiohttp.ClientSession.get') as patched_request:

            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(connect_response)

            await self.connector.connect(opsdroid)

            self.assertLogs('_LOGGER', 'debug')
            self.assertNotEqual(200, patched_request.status)
            self.assertTrue(patched_request.called)

    async def test_connect_failure(self):
        result = amock.MagicMock()
        result.status = 401

        with OpsDroid() as opsdroid, \
            amock.patch('aiohttp.ClientSession.get') as patched_request:

            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(result)

            await self.connector.connect(opsdroid)
            self.assertLogs('_LOGGER', 'error')

    async def test_get_message(self):
        connector_group = RocketChat({
                'name': 'rocket.chat',
                'token': 'test',
                'user-id': 'userID',
                'group': "test"
            })
        response = amock.Mock()
        response.status = 200
        response.json = amock.CoroutineMock()
        response.return_value = {
            'messages': [
                {
                    "_id": "ZbhuIO764jOIu",
                    "rid": "Ipej45JSbfjt9",
                    "msg": "hows it going",
                    "ts": "2018-05-11T16:05:41.047Z",
                    "u": {
                        "_id": "ZbhuIO764jOIu",
                        "username": "FabioRosado",
                        "name": "Fábio Rosado"
                    },
                    "_updatedAt": "2018-05-11T16:05:41.489Z",
                    "editedBy": None,
                    "editedAt": None,
                    "emoji": None,
                    "avatar": None,
                    "alias": None,
                    "customFields": None,
                    "attachments": None,
                    "mentions": [],
                    "channels": []
                }
                ]}

        with OpsDroid() as opsdroid, \
            amock.patch('aiohttp.ClientSession.get') as patched_request, \
            amock.patch.object(connector_group, '_parse_message') \
                as mocked_parse_message:

            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(response)

            await connector_group._get_message(opsdroid)

            self.assertTrue(patched_request.called)
            self.assertTrue(mocked_parse_message.called)

    async def test_parse_message(self):
        response = {
            'messages': [
                {
                    "_id": "ZbhuIO764jOIu",
                    "rid": "Ipej45JSbfjt9",
                    "msg": "hows it going",
                    "ts": "2018-05-11T16:05:41.047Z",
                    "u": {
                        "_id": "ZbhuIO764jOIu",
                        "username": "FabioRosado",
                        "name": "Fábio Rosado"
                    },
                    "_updatedAt": "2018-05-11T16:05:41.489Z",
                    "editedBy": None,
                    "editedAt": None,
                    "emoji": None,
                    "avatar": None,
                    "alias": None,
                    "customFields": None,
                    "attachments": None,
                    "mentions": [],
                    "channels": []
                }
                ]}

        with OpsDroid() as opsdroid, \
                amock.patch('opsdroid.core.OpsDroid.parse') as mocked_parse:
            await self.connector._parse_message(opsdroid, response)
            self.assertLogs('_LOGGER', 'debug')
            self.assertTrue(mocked_parse.called)
            self.assertEqual("2018-05-11T16:05:41.047Z",
                             self.connector.latest_update)


    async def test_listen(self):
        self.connector.side_effect = Exception()
        await self.connector.listen(amock.CoroutineMock())

    async def test_get_message_failure(self):
        listen_response = amock.Mock()
        listen_response.status = 401

        with OpsDroid() as opsdroid, \
            amock.patch('aiohttp.ClientSession.get') as patched_request:

            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(listen_response)
            await self.connector._get_message(opsdroid)
            self.assertLogs('_LOGGER', 'error')
            self.assertEqual(False, self.connector.listening)

    async def test_respond(self):
        post_response = amock.Mock()
        post_response.status = 200

        with OpsDroid() as opsdroid, \
            amock.patch('aiohttp.ClientSession.post') as patched_request:

            self.assertTrue(opsdroid.__class__.instances)
            test_message = Message(text="This is a test",
                                   user="opsdroid",
                                   room="test",
                                   connector=self.connector)

            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(post_response)
            await test_message.respond("Response")
            self.assertTrue(patched_request.called)
            self.assertLogs('_LOGGER', 'debug')

    async def test_respond_failure(self):
        post_response = amock.Mock()
        post_response.status = 401

        with OpsDroid() as opsdroid, \
            amock.patch('aiohttp.ClientSession.post') as patched_request:

            self.assertTrue(opsdroid.__class__.instances)
            test_message = Message(text="This is a test",
                                   user="opsdroid",
                                   room="test",
                                   connector=self.connector)

            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(post_response)
            await test_message.respond("Response")
            self.assertLogs('_LOGGER', 'debug')
