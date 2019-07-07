"""Tests for the ConnectorTelegram class."""
import asyncio
import aiohttp
import contextlib
import unittest
import asynctest
import asynctest.mock as amock

from opsdroid import events
from opsdroid.core import OpsDroid
from opsdroid.connector.telegram import ConnectorTelegram
from opsdroid.events import Message, Image
from opsdroid.__main__ import configure_lang


class TestConnectorTelegram(unittest.TestCase):
    """Test the opsdroid Telegram connector class."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        configure_lang({})

    def test_init(self):
        """Test that the connector is initialised properly."""
        connector = ConnectorTelegram(
            {"name": "telegram", "token": "test", "update-interval": 0.2},
            opsdroid=OpsDroid(),
        )
        self.assertEqual(None, connector.default_target)
        self.assertEqual("telegram", connector.name)
        self.assertEqual(0.2, connector.update_interval)

    def test_missing_token(self):
        """Test that attempt to connect without info raises an error."""
        ConnectorTelegram({}, opsdroid=OpsDroid())
        self.assertLogs("_LOGGER", "error")


class TestConnectorTelegramAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid Telegram connector class."""

    def setUp(self):
        configure_lang({})
        self.connector = ConnectorTelegram(
            {
                "name": "telegram",
                "token": "bot:765test",
                "whitelisted-users": ["user", "test", "AnUser"],
            },
            opsdroid=OpsDroid(),
        )
        with amock.patch("aiohttp.ClientSession") as mocked_session:
            self.connector.session = mocked_session

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
                "username": "opsdroid_bot",
            },
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

    async def test_parse_message_username(self):
        response = {
            "result": [
                {
                    "update_id": 427647860,
                    "message": {
                        "message_id": 12,
                        "from": {
                            "id": 649671308,
                            "is_bot": False,
                            "first_name": "A",
                            "last_name": "User",
                            "username": "user",
                            "language_code": "en-GB",
                        },
                        "chat": {
                            "id": 649671308,
                            "first_name": "A",
                            "last_name": "User",
                            "username": "user",
                            "type": "private",
                        },
                        "date": 1538756863,
                        "text": "Hello",
                    },
                }
            ]
        }

        with amock.patch("opsdroid.core.OpsDroid.parse") as mocked_parse:
            await self.connector._parse_message(response)
            self.assertTrue(mocked_parse.called)

    async def test_parse_edited_message(self):
        response = {
            "result": [
                {
                    "update_id": 246644499,
                    "edited_message": {
                        "message_id": 150,
                        "from": {
                            "id": 245245245,
                            "is_bot": False,
                            "first_name": "IOBreaker",
                            "language_code": "en",
                        },
                        "chat": {
                            "id": 245245245,
                            "first_name": "IOBreaker",
                            "type": "private",
                        },
                        "date": 1551797346,
                        "edit_date": 1551797365,
                        "text": "hello2",
                    },
                }
            ]
        }
        response_copy = list(response)
        mocked_status = amock.CoroutineMock()
        mocked_status.status = 200
        with amock.patch(
            "opsdroid.core.OpsDroid.parse"
        ) as mocked_parse, amock.patch.object(
            self.connector.session, "post"
        ) as patched_request:
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(mocked_status)
            self.assertTrue(response["result"][0].get("edited_message"))
            await self.connector._parse_message(response)

    async def test_parse_message_channel(self):
        response = {
            "result": [
                {
                    "update_id": 427647860,
                    "message": {
                        "message_id": 12,
                        "from": {
                            "id": 649671308,
                            "is_bot": False,
                            "first_name": "A",
                            "last_name": "User",
                            "username": "user",
                            "language_code": "en-GB",
                        },
                        "chat": {
                            "id": 649671308,
                            "first_name": "A",
                            "last_name": "User",
                            "username": "user",
                            "type": "channel",
                        },
                        "date": 1538756863,
                        "text": "Hello",
                    },
                }
            ]
        }

        with amock.patch("opsdroid.core.OpsDroid.parse"):
            await self.connector._parse_message(response)
            self.assertLogs("_LOGGER", "debug")

    async def test_parse_message_first_name(self):
        response = {
            "result": [
                {
                    "update_id": 427647860,
                    "message": {
                        "message_id": 12,
                        "from": {
                            "id": 649671308,
                            "is_bot": False,
                            "first_name": "AnUser",
                            "type": "private",
                            "language_code": "en-GB",
                        },
                        "chat": {
                            "id": 649671308,
                            "first_name": "AnUser",
                            "type": "private",
                        },
                        "date": 1538756863,
                        "text": "Hello",
                    },
                }
            ]
        }
        with amock.patch("opsdroid.core.OpsDroid.parse") as mocked_parse:
            await self.connector._parse_message(response)
            self.assertTrue(mocked_parse.called)

    async def test_parse_message_bad_result(self):
        response = {
            "result": [
                {
                    "update_id": 427647860,
                    "message": {
                        "message_id": 12,
                        "from": {
                            "id": 649671308,
                            "is_bot": False,
                            "first_name": "test",
                            "language_code": "en-GB",
                        },
                        "chat": {
                            "id": 649671308,
                            "first_name": "test",
                            "type": "private",
                        },
                        "date": 1538756863,
                    },
                }
            ]
        }

        await self.connector._parse_message(response)
        self.assertLogs("error", "_LOGGER")

    async def test_parse_message_unauthorized(self):
        self.connector.config["whitelisted-users"] = ["user", "test"]
        response = {
            "result": [
                {
                    "update_id": 427647860,
                    "message": {
                        "message_id": 12,
                        "from": {
                            "id": 649671308,
                            "is_bot": False,
                            "first_name": "A",
                            "last_name": "User",
                            "username": "a_user",
                            "language_code": "en-GB",
                        },
                        "chat": {
                            "id": 649671308,
                            "first_name": "A",
                            "last_name": "User",
                            "username": "a_user",
                            "type": "private",
                        },
                        "date": 1538756863,
                        "text": "Hello",
                    },
                }
            ]
        }

        self.assertEqual(self.connector.config["whitelisted-users"], ["user", "test"])

        message_text = "Sorry, you're not allowed to speak with this bot."

        with amock.patch.object(self.connector, "send") as mocked_respond:
            await self.connector._parse_message(response)
            self.assertTrue(mocked_respond.called)
            self.assertTrue(mocked_respond.called_with(message_text))

    async def test_get_messages(self):
        listen_response = amock.Mock()
        listen_response.status = 200
        listen_response.json = amock.CoroutineMock()
        listen_response.return_value = {
            "result": [
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
                            "language_code": "en-GB",
                        },
                        "chat": {
                            "id": 639889348,
                            "first_name": "Fabio",
                            "last_name": "Rosado",
                            "username": "FabioRosado",
                            "type": "private",
                        },
                        "date": 1538756863,
                        "text": "Hello",
                    },
                }
            ]
        }

        with amock.patch.object(
            self.connector.session, "get"
        ) as patched_request, amock.patch.object(
            self.connector, "_parse_message"
        ) as mocked_parse_message:

            self.connector.latest_update = 54

            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(listen_response)
            await self.connector._get_messages()
            self.assertTrue(patched_request.called)
            self.assertLogs("_LOGGER", "debug")
            self.assertTrue(mocked_parse_message.called)

    async def test_delete_webhook(self):
        response = amock.Mock()
        response.status = 200

        with amock.patch.object(self.connector.session, "get") as mock_request:
            mock_request.return_value = asyncio.Future()
            mock_request.return_value.set_result(response)

            await self.connector.delete_webhook()
            self.assertLogs("_LOGGER", "debug")

    async def test_get_message_webhook(self):
        response = amock.Mock()
        response.status = 409

        with amock.patch.object(
            self.connector.session, "get"
        ) as mock_request, amock.patch.object(
            self.connector, "delete_webhook"
        ) as mock_method:
            mock_request.return_value = asyncio.Future()
            mock_request.return_value.set_result(response)

            await self.connector._get_messages()
            self.assertLogs("_LOGGER", "info")
            self.assertTrue(mock_method.called)

    async def test_delete_webhook_failure(self):
        response = amock.Mock()
        response.status = 401

        with amock.patch.object(self.connector.session, "get") as mock_request:
            mock_request.return_value = asyncio.Future()
            mock_request.return_value.set_result(response)

            await self.connector.delete_webhook()
            self.assertLogs("_LOGGER", "debug")

    async def test_get_messages_failure(self):
        listen_response = amock.Mock()
        listen_response.status = 401

        with amock.patch.object(self.connector.session, "get") as patched_request:

            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(listen_response)
            await self.connector._get_messages()
            self.assertLogs("_LOGGER", "error")

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
                target={"id": 12404},
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
                target={"id": 12404},
                connector=self.connector,
            )

            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(post_response)
            await test_message.respond("Response")
            self.assertLogs("_LOGGER", "debug")

    async def test_respond_image(self):
        post_response = amock.Mock()
        post_response.status = 200

        gif_bytes = (
            b"GIF89a\x01\x00\x01\x00\x00\xff\x00,"
            b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;"
        )

        image = Image(file_bytes=gif_bytes, target={"id": "123"})

        with amock.patch.object(self.connector.session, "post") as patched_request:

            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(post_response)

            await self.connector.send_image(image)
            self.assertTrue(patched_request.called)

    async def test_respond_image_failure(self):
        post_response = amock.Mock()
        post_response.status = 400

        gif_bytes = (
            b"GIF89a\x01\x00\x01\x00\x00\xff\x00,"
            b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;"
        )

        image = Image(file_bytes=gif_bytes, target={"id": "123"})

        with amock.patch.object(self.connector.session, "post") as patched_request:

            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(post_response)

            await self.connector.send_image(image)
            self.assertLogs("_LOOGER", "debug")

    async def test_listen(self):
        with amock.patch.object(
            self.connector.loop, "create_task"
        ) as mocked_task, amock.patch.object(
            self.connector._closing, "wait"
        ) as mocked_event:
            mocked_event.return_value = asyncio.Future()
            mocked_event.return_value.set_result(True)
            mocked_task.return_value = asyncio.Future()
            await self.connector.listen()

            self.assertTrue(mocked_event.called)
            self.assertTrue(mocked_task.called)

    async def test_disconnect(self):
        with amock.patch.object(self.connector.session, "close") as mocked_close:
            mocked_close.return_value = asyncio.Future()
            mocked_close.return_value.set_result(True)

            await self.connector.disconnect()
            self.assertFalse(self.connector.listening)
            self.assertTrue(self.connector.session.closed())
            self.assertEqual(self.connector._closing.set(), None)
