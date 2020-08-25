"""Tests for the RocketChat class."""
import asyncio
import unittest
import contextlib
import asynctest
import asynctest.mock as amock

from opsdroid.core import OpsDroid
from opsdroid.connector.rocketchat import RocketChat
from opsdroid.events import Message
from opsdroid.cli.start import configure_lang


class TestRocketChat(unittest.TestCase):
    """Test the opsdroid RocketChat connector class."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        configure_lang({})

    def test_init(self):
        """Test that the connector is initialised properly."""
        connector = RocketChat(
            {
                "name": "rocket.chat",
                "token": "test",
                "user-id": "userID",
                "update-interval": 0.1,
            },
            opsdroid=OpsDroid(),
        )
        self.assertEqual("general", connector.default_target)
        self.assertEqual("rocket.chat", connector.name)

    def test_missing_token(self):
        """Test that attempt to connect without info raises an error."""

        RocketChat({})
        self.assertLogs("_LOGGER", "error")


class TestConnectorRocketChatAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid RocketChat connector class."""

    def setUp(self):
        configure_lang({})
        self.connector = RocketChat(
            {
                "name": "rocket.chat",
                "token": "test",
                "user-id": "userID",
                "default_target": "test",
            },
            opsdroid=OpsDroid(),
        )

        self.connector.latest_update = "2018-10-08T12:57:37.126Z"

        with amock.patch("aiohttp.ClientSession") as mocked_session:
            self.connector.session = mocked_session

    async def test_connect(self):
        connect_response = amock.Mock()
        connect_response.status = 200
        connect_response.json = amock.CoroutineMock()
        connect_response.return_value = {
            "_id": "3vABZrQgDzfcz7LZi",
            "name": "Fábio Rosado",
            "emails": [{"address": "fabioglrosado@gmail.com", "verified": True}],
            "status": "online",
            "statusConnection": "online",
            "username": "FabioRosado",
            "utcOffset": 1,
            "active": True,
            "roles": ["user"],
            "settings": {},
            "email": "fabioglrosado@gmail.com",
            "success": True,
        }

        with amock.patch("aiohttp.ClientSession.get") as patched_request:

            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(connect_response)

            await self.connector.connect()

            self.assertLogs("_LOGGER", "debug")
            self.assertNotEqual(200, patched_request.status)
            self.assertTrue(patched_request.called)

    async def test_connect_failure(self):
        result = amock.MagicMock()
        result.status = 401

        with amock.patch("aiohttp.ClientSession.get") as patched_request:

            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(result)

            await self.connector.connect()
            self.assertLogs("_LOGGER", "error")

    async def test_get_message(self):
        self.connector.group = "test"
        response = amock.Mock()
        response.status = 200
        response.json = amock.CoroutineMock()
        response.return_value = {
            "messages": [
                {
                    "_id": "ZbhuIO764jOIu",
                    "rid": "Ipej45JSbfjt9",
                    "msg": "hows it going",
                    "ts": "2018-05-11T16:05:41.047Z",
                    "u": {
                        "_id": "ZbhuIO764jOIu",
                        "username": "FabioRosado",
                        "name": "Fábio Rosado",
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
                    "channels": [],
                }
            ]
        }

        with amock.patch.object(
            self.connector.session, "get"
        ) as patched_request, amock.patch.object(
            self.connector, "_parse_message"
        ) as mocked_parse_message, amock.patch(
            "asyncio.sleep"
        ) as mocked_sleep:

            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(response)

            await self.connector._get_message()

            self.assertTrue(patched_request.called)
            self.assertTrue(mocked_parse_message.called)
            self.assertTrue(mocked_sleep.called)
            self.assertLogs("_LOGGER", "debug")

    async def test_parse_message(self):
        response = {
            "messages": [
                {
                    "_id": "ZbhuIO764jOIu",
                    "rid": "Ipej45JSbfjt9",
                    "msg": "hows it going",
                    "ts": "2018-05-11T16:05:41.047Z",
                    "u": {
                        "_id": "ZbhuIO764jOIu",
                        "username": "FabioRosado",
                        "name": "Fábio Rosado",
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
                    "channels": [],
                }
            ]
        }

        with amock.patch.object(self.connector, "get_messages_loop"), amock.patch(
            "opsdroid.core.OpsDroid.parse"
        ) as mocked_parse:
            await self.connector._parse_message(response)
            self.assertLogs("_LOGGER", "debug")
            self.assertTrue(mocked_parse.called)
            self.assertEqual("2018-05-11T16:05:41.047Z", self.connector.latest_update)

    async def test_listen(self):
        with amock.patch.object(
            self.connector.loop, "create_task"
        ) as mocked_task, amock.patch.object(
            self.connector._closing, "wait"
        ) as mocked_event, amock.patch.object(
            self.connector, "get_messages_loop"
        ):
            mocked_event.return_value = asyncio.Future()
            mocked_event.return_value.set_result(True)
            mocked_task.return_value = asyncio.Future()
            await self.connector.listen()

            self.assertTrue(mocked_event.called)
            self.assertTrue(mocked_task.called)

    async def test_get_message_failure(self):
        listen_response = amock.Mock()
        listen_response.status = 401

        with amock.patch.object(self.connector.session, "get") as patched_request:

            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(listen_response)
            await self.connector._get_message()
            self.assertLogs("_LOGGER", "error")
            self.assertEqual(False, self.connector.listening)

    async def test_get_messages_loop(self):
        self.connector._get_messages = amock.CoroutineMock()
        self.connector._get_messages.side_effect = Exception()
        with contextlib.suppress(Exception):
            await self.connector.get_messages_loop()

    async def test_respond(self):
        post_response = amock.Mock()
        post_response.status = 200

        with OpsDroid() as opsdroid, amock.patch.object(
            self.connector.session, "post"
        ) as patched_request:

            self.assertTrue(opsdroid.__class__.instances)
            test_message = Message(
                text="This is a test",
                user="opsdroid",
                target="test",
                connector=self.connector,
            )

            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(post_response)
            await test_message.respond("Response")
            self.assertTrue(patched_request.called)
            self.assertLogs("_LOGGER", "debug")

    async def test_respond_failure(self):
        post_response = amock.Mock()
        post_response.status = 401

        with OpsDroid() as opsdroid, amock.patch.object(
            self.connector.session, "post"
        ) as patched_request:

            self.assertTrue(opsdroid.__class__.instances)
            test_message = Message(
                text="This is a test",
                user="opsdroid",
                target="test",
                connector=self.connector,
            )

            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(post_response)
            await test_message.respond("Response")
            self.assertLogs("_LOGGER", "debug")

    async def test_disconnect(self):
        with amock.patch.object(self.connector.session, "close") as mocked_close:
            mocked_close.return_value = asyncio.Future()
            mocked_close.return_value.set_result(True)

            await self.connector.disconnect()
            self.assertFalse(self.connector.listening)
            self.assertTrue(self.connector.session.closed())
            self.assertEqual(self.connector._closing.set(), None)
