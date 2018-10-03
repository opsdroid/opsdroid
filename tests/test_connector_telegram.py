"""Tests for the ConnectorTelegram class."""
import asyncio
import unittest
import unittest.mock as mock
import asynctest
import asynctest.mock as amock

from opsdroid.core import OpsDroid
from opsdroid.connector.telegram import ConnectorTelegram
from opsdroid.message import  Message


class AsyncContextManagerMock(amock.MagicMock):
    async def __aenter__(self):
        return self.aenter

    async def __aexit__(self, *args):
        pass


class TestConnectorSlack(unittest.TestCase):
    """Test the opsdroid Telegram connector class."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()

    def test_init(self):
        """Test that the connector is initialised properly."""
        connector = ConnectorTelegram({
            'name': 'telegram',
            'token': 'test',
        })
        self.assertEqual("general", connector.default_room)
        self.assertEqual("rocket.chat", connector.name)

    def test_missing_token(self):
        """Test that attempt to connect without info raises an error."""
        with mock.patch('opsdroid.connector.telegram._LOGGER.error') \
                as logmock:
            ConnectorTelegram({})
            self.assertTrue(logmock.called)


class TestConnectorConnectorTelegramAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid Telegram connector class."""

    async def test_connect(self):
        connect_response = amock.Mock()
        connect_response.status = 200

        with OpsDroid() as opsdroid, \
            amock.patch('aiohttp.ClientSession.get',
                        new=AsyncContextManagerMock) as patched_request, \
            amock.patch('opsdroid.connector.telegram._LOGGER.debug',) \
                as logmock:
            connector = ConnectorTelegram({
                'name': 'telegram',
                'token': 'test',
            })
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(connect_response)
            await connector.connect(opsdroid)
            self.assertTrue(logmock.called)
            self.assertTrue(patched_request.called)

    async def test_connect_failure(self):
        connector = ConnectorTelegram({
            'name': 'telegram',
            'token': 'test',
        })
        opsdroid = amock.CoroutineMock()
        opsdroid.eventloop = self.loop
        result = amock.MagicMock()
        result.json = amock.CoroutineMock()
        result.status = 401

        with amock.patch('aiohttp.ClientSession.get') as mocked_session:
            mocked_session.return_value.json = result
            with self.assertRaises(Exception):
                await connector.connect(opsdroid)
                self.assertFalse(mocked_session.called)

    async def test_listen_loop_channel(self):
        listen_response = amock.Mock()
        listen_response.status = 200
        listen_response.return_value = {
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
            amock.patch('aiohttp.ClientSession.get',
                        new=AsyncContextManagerMock) as patched_request:
            connector = ConnectorTelegram({
                'name': 'telegram',
                'token': 'test',
            })
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(listen_response)
            await connector.listen(opsdroid)
            self.assertTrue(patched_request.called)

    async def test_listen_loop_group(self):
        listen_response = amock.Mock()
        listen_response.status = 200
        listen_response.return_value.json = {
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
            amock.patch('aiohttp.ClientSession.get',
                        new=AsyncContextManagerMock) as patched_request:
            connector = ConnectorTelegram({
                'name': 'telegram',
                'token': 'test',
            })
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(listen_response)
            await connector.listen(opsdroid)
            self.assertTrue(patched_request.called)

    async def test_listen_loop_failure(self):
        listen_response = amock.Mock()
        listen_response.status = 401

        with OpsDroid() as opsdroid, \
            amock.patch('aiohttp.ClientSession.get',
                        new=AsyncContextManagerMock) as patched_request, \
            amock.patch('opsdroid.connector.telegram._LOGGER.error') as \
                logmock:
            connector = ConnectorTelegram({
                'name': 'rocket.chat',
                'token': 'test',
                'user-id': 'userID',
                'default_room': "test"
            })
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(listen_response)
            await connector.listen(opsdroid)
            self.assertTrue(logmock.called)
            self.assertTrue(patched_request.called)

    async def test_respond(self):
        post_response = amock.Mock()
        post_response.status = 200

        with OpsDroid() as opsdroid, \
            amock.patch('aiohttp.ClientSession.post',
                        new=AsyncContextManagerMock) as patched_request:
            self.assertTrue(opsdroid.__class__.instances)
            connector = ConnectorTelegram({
                'name': 'telegram',
                'token': 'test',
            })
            test_message = Message(text="This is a test",
                                   user="opsdroid",
                                   room="test",
                                   connector=connector)

            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(post_response)
            await test_message.respond("Response")
            self.assertTrue(patched_request.called)

    async def test_respond_failure(self):
        post_response = amock.Mock()
        post_response.status = 401

        with OpsDroid() as opsdroid, \
            amock.patch('opsdroid.connector.telegram._LOGGER.debug', ) \
                    as logmock, \
            amock.patch('aiohttp.ClientSession.post',
                        new=AsyncContextManagerMock) as patched_request:
            self.assertTrue(opsdroid.__class__.instances)
            connector = ConnectorTelegram({
                'name': 'telegram',
                'token': 'test',
            })
            test_message = Message(text="This is a test",
                                   user="opsdroid",
                                   room="test",
                                   connector=connector)

            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(post_response)
            await test_message.respond("Response")
            self.assertTrue(logmock.called)
            self.assertTrue(patched_request.called)
