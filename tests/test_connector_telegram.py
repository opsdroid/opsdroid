"""Tests for the ConnectorTelegram class."""
import asyncio
import unittest
import unittest.mock as mock
import asynctest
import asynctest.mock as amock

from opsdroid.core import OpsDroid
from opsdroid.connector.telegram import ConnectorTelegram
from opsdroid.message import Message


class TestConnectorTelegram(unittest.TestCase):
    """Test the opsdroid Telegram connector class."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()

    def test_init(self):
        """Test that the connector is initialised properly."""
        connector = ConnectorTelegram({
            'name': 'telegram',
            'token': 'test',
        })
        self.assertEqual(None, connector.default_room)
        self.assertEqual("telegram", connector.name)

    def test_missing_token(self):
        """Test that attempt to connect without info raises an error."""
        ConnectorTelegram({})
        self.assertLogs('_LOGGER', 'error')


class TestConnectorTelegramAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid Telegram connector class."""

    def setUp(self):
        self.connector = ConnectorTelegram({
                'name': 'telegram',
                'token': 'bot:765test',
                'whitelisted-users': ['user', 'test']
            })

    async def test_connect(self):
        connect_response = amock.Mock()
        connect_response.status = 200
        connect_response.json = amock.CoroutineMock()
        connect_response.return_value = {
            "ok": True,
            "result": {
                "id": 635392558,
                "is_bot": True,
                "first_name": "opsdroid",
                "username": "opsdroid_bot"
            }
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

    async def test_parse_message(self):
        response = {
            "update_id": 427647860,
            "message": {
                "message_id": 12,
                "from": {
                    "id": 649671308,
                    "is_bot": False,
                    "first_name": "A",
                    "last_name": "User",
                    "username": "user",
                    "language_code": "en-GB"
                },
                "chat": {
                    "id": 649671308,
                    "first_name": "A",
                    "last_name": "User",
                    "username": "user",
                    "type": "private"
                },
                "date": 1538756863,
                "text": "Hello"
            }
        }

        with OpsDroid() as opsdroid, \
                amock.patch('opsdroid.core.OpsDroid.parse') as mocked_parse:
            await self.connector._parse_message(opsdroid, response)
            self.assertTrue(mocked_parse.called)

    async def test_parse_message_unauthorized(self):
        self.connector.config['whitelisted-users'] = ['user', 'test']
        response = {
            "update_id": 427647860,
            "message": {
                "message_id": 12,
                "from": {
                    "id": 649671308,
                    "is_bot": False,
                    "first_name": "A",
                    "last_name": "User",
                    "username": "a_user",
                    "language_code": "en-GB"
                },
                "chat": {
                    "id": 649671308,
                    "first_name": "A",
                    "last_name": "User",
                    "username": "a_user",
                    "type": "private"
                },
                "date": 1538756863,
                "text": "Hello"
            }
        }

        self.assertEqual(
            self.connector.config['whitelisted-users'], ['user', 'test'])

        message_text = "Sorry, you're not allowed to speak with this bot."

        with OpsDroid() as opsdroid, \
                amock.patch.object(self.connector, 'respond') \
                as mocked_respond:
            await self.connector._parse_message(opsdroid, response)
            self.assertTrue(mocked_respond.called)
            self.assertTrue(mocked_respond.called_with(message_text))

    async def test_get_messages(self):
        listen_response = amock.Mock()
        listen_response.status = 200
        listen_response.json = amock.CoroutineMock()
        listen_response.return_value = {"result": [
            {
                "update_id": 427647860,
                "message": {
                    "message_id": 54,
                    "from": {
                        "id": 639889348,
                        "is_bot": False,
                        "first_name": "Fabio",
                        "last_name": "Rosado",
                        "username": "FabioRosado",
                        "language_code": "en-GB"
                    },
                    "chat": {
                        "id": 639889348,
                        "first_name": "Fabio",
                        "last_name": "Rosado",
                        "username": "FabioRosado",
                        "type": "private"
                    },
                    "date": 1538756863,
                    "text": "Hello"
                }
            }
        ]}

        with OpsDroid() as opsdroid, \
            amock.patch('aiohttp.ClientSession.get') as patched_request, \
            amock.patch.object(self.connector, '_parse_message') \
                as mocked_parse_message:

            self.connector.latest_update = 54

            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(listen_response)
            await self.connector._get_messages(opsdroid)
            self.assertTrue(patched_request.called)
            self.assertLogs('_LOGGER', 'debug')
            # self.assertTrue(mocked_parse_message.called)

    async def test_get_messages_failure(self):
        listen_response = amock.Mock()
        listen_response.status = 401

        with OpsDroid() as opsdroid, \
            amock.patch('aiohttp.ClientSession.get') as patched_request:

            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(listen_response)
            await self.connector._get_messages(opsdroid)
            self.assertLogs('_LOGGER', 'error')

    async def test_listen(self):
        self.connector.listening = amock.CoroutineMock()
        self.connector.listening.side_effect = Exception()
        await self.connector.listen(amock.CoroutineMock())

    async def test_respond(self):
        post_response = amock.Mock()
        post_response.status = 200

        with OpsDroid() as opsdroid, \
            amock.patch('aiohttp.ClientSession.post') as patched_request:

            self.assertTrue(opsdroid.__class__.instances)
            test_message = Message(text="This is a test",
                                   user="opsdroid",
                                   room={"id": 12404},
                                   connector=self.connector)

            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(post_response)
            await test_message.respond("Response")
            self.assertTrue(patched_request.called)
            self.assertLogs("_LOGGER", "debug")

    async def test_respond_failure(self):
        post_response = amock.Mock()
        post_response.status = 401

        with OpsDroid() as opsdroid, \
            amock.patch('aiohttp.ClientSession.post') as patched_request:

            self.assertTrue(opsdroid.__class__.instances)
            test_message = Message(text="This is a test",
                                   user="opsdroid",
                                   room={"id": 12404},
                                   connector=self.connector)

            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(post_response)
            await test_message.respond("Response")
            self.assertLogs('_LOGGER', 'debug')
