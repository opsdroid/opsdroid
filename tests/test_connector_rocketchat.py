"""Tests for the ConnectorSlack class."""
import asyncio
import unittest
import unittest.mock as mock
import asynctest
import asynctest.mock as amock

from opsdroid.connector.rocketchat import RocketChat
from opsdroid.message import  Message


class TestConnectorSlack(unittest.TestCase):
    """Test the opsdroid Slack connector class."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()

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
        with mock.patch('opsdroid.connector.rocketchat._LOGGER.error') \
                as logmock:
            RocketChat({})
            self.assertTrue(logmock.called)


class TestConnectorRocketChatAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid Slack connector class."""

    async def test_connect(self):
        connector = RocketChat({
            'name': 'rocket.chat',
            'token': 'test',
            'user-id': 'userID'
        })
        opsdroid = amock.CoroutineMock()
        opsdroid.eventloop = self.loop
        result = amock.MagicMock()
        result.json = amock.CoroutineMock()
        result.json.return_value = {
            "_id": "1bhtKOIS9jpLKI",
            "name": "Opsdroid",
            "emails": [
                {
                    "address": "opsdroid@opsdroid.op",
                    "verified": True
                }
            ],
            "status": "online",
            "statusConnection": "online",
            "username": "opsdroid",
            "utcOffset": 1,
            "active": True,
            "roles": [
                "user"
            ],
            "settings": {
                "preferences": {}
            },
            "email": "opsdroid@opsdroid.op",
            "success": True
        }
        result.status = 200

        with amock.patch('aiohttp.ClientSession.get') as mocked_session:
            mocked_session.return_value.json = result
            with self.assertRaises(Exception):
                await connector.connect(opsdroid)
                self.assertFalse(mocked_session.called)

    async def test_listen_loop(self):
        """Test that listening consumes from the socket."""
        connector = RocketChat({
            'name': 'rocket.chat',
            'access-token': 'test',
            'user-id': 'userID'
        })
        opsdroid = amock.CoroutineMock()
        opsdroid.eventloop = self.loop
        result = amock.MagicMock()
        result.json = amock.CoroutineMock()
        result.json.return_value =         {
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

        with amock.patch('aiohttp.ClientSession.get') as mocked_session:
            mocked_session.return_value = result
            with self.assertRaises(Exception):
                await connector.listen(opsdroid)
                self.assertTrue(mocked_session.called)

    async def test_respond(self):
        connector = RocketChat({
            'name': 'rocket.chat',
            'access-token': 'test',
            'user-id': 'userID'
        })

        with amock.patch('aiohttp.ClientSession.post') as mocked_session:
            with self.assertRaises(Exception):
                await connector.respond(
                    Message("test", "user", "room", connector))
                self.assertTrue(mocked_session.called)
