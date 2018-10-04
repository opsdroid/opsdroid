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
        with mock.patch('opsdroid.connector.telegram._LOGGER.error') \
                as logmock:
            ConnectorTelegram({})
            self.assertTrue(logmock.called)


class TestConnectorTelegramAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid Telegram connector class."""

    def setUp(self):
        self.connector = ConnectorTelegram({
                'name': 'telegram',
                'token': 'test',
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
            amock.patch('aiohttp.ClientSession.get') as patched_request, \
            amock.patch('opsdroid.connector.telegram._LOGGER.debug',) \
                as logmock:

            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(connect_response)
            await self.connector.connect(opsdroid)
            self.assertTrue(logmock.called)
            self.assertNotEqual(200, patched_request.status)
            self.assertTrue(patched_request.called)

    async def test_connect_failure(self):
        result = amock.MagicMock()
        result.status = 401

        with OpsDroid() as opsdroid, \
            amock.patch('aiohttp.ClientSession.get') as patched_request, \
            amock.patch('opsdroid.connector.telegram._LOGGER.error',) \
                as logmock:

            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(result)

            await self.connector.connect(opsdroid)
            self.assertTrue(logmock.called)

    # async def test_listen_loop(self):
    #     listen_response = amock.Mock()
    #     listen_response.status = 200
    #     listen_response.json = amock.CoroutineMock()
    #     listen_response.return_value =
    #
    #     with OpsDroid() as opsdroid, \
    #         amock.patch('aiohttp.ClientSession.get') as patched_request, \
    #         amock.patch('opsdroid.connector.telegram._LOGGER.debug',) \
    #             as logmock:
    #
    #         patched_request.return_value = asyncio.Future()
    #         patched_request.return_value.set_result(listen_response)
    #         await self.connector.listen(opsdroid)
    #         self.assertTrue(patched_request.called)
    #         self.assertTrue(logmock.called)

    async def test_listen_loop_failure(self):
        listen_response = amock.Mock()
        listen_response.status = 401

        with OpsDroid() as opsdroid, \
            amock.patch('aiohttp.ClientSession.get') as patched_request, \
            amock.patch('opsdroid.connector.telegram._LOGGER.error',) \
                as logmock:

            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(listen_response)
            await self.connector.listen(opsdroid)
            self.assertTrue(logmock.called)

    async def test_respond(self):
        post_response = amock.Mock()
        post_response.status = 200

        with OpsDroid() as opsdroid, \
            amock.patch('aiohttp.ClientSession.post') as patched_request, \
            amock.patch('opsdroid.connector.telegram._LOGGER.debug') \
                as logmock:

            self.assertTrue(opsdroid.__class__.instances)
            test_message = Message(text="This is a test",
                                   user="opsdroid",
                                   room={"id": 12404},
                                   connector=self.connector)

            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(post_response)
            await test_message.respond("Response")
            self.assertTrue(patched_request.called)
            self.assertTrue(logmock.called)

    async def test_respond_failure(self):
        post_response = amock.Mock()
        post_response.status = 401

        with OpsDroid() as opsdroid, \
            amock.patch('aiohttp.ClientSession.post') as patched_request, \
            amock.patch('opsdroid.connector.telegram._LOGGER.debug') \
                as logmock:

            self.assertTrue(opsdroid.__class__.instances)
            test_message = Message(text="This is a test",
                                   user="opsdroid",
                                   room={"id": 12404},
                                   connector=self.connector)

            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(post_response)
            await test_message.respond("Response")
            self.assertTrue(logmock.called)

