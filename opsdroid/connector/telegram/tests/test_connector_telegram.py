import logging
import asyncio
import pytest
import asynctest.mock as amock


from opsdroid.connector.telegram import ConnectorTelegram

# import opsdroid.connector.telegram.events as telegram_events
from opsdroid.events import (
    Message,
    Image,
    File,
    # EditedMessage,
    # Reply,
    # JoinGroup,
    # LeaveGroup,
    # PinMessage,
)


connector_config = {
    "token": "test:token",
}


def test_init_no_base_url(opsdroid, caplog):
    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)
    caplog.set_level(logging.ERROR)

    assert connector.name == "telegram"
    assert connector.token == "test:token"
    assert connector.whitelisted_users is None
    assert connector.webhook_secret is not None
    assert connector.base_url is None
    assert "base-url is missing" in caplog.text


def test_init(opsdroid):
    config = {
        "token": "test:token",
        "whitelisted-users": ["bob", 1234],
        "bot-name": "bot McBotty",
    }

    connector = ConnectorTelegram(config, opsdroid=opsdroid)

    opsdroid.config["web"] = {"base-url": "https://test.com"}

    assert connector.name == "telegram"
    assert connector.token == "test:token"
    assert connector.whitelisted_users == ["bob", 1234]
    assert connector.bot_name == "bot McBotty"
    assert connector.webhook_secret is not None


def test_get_user_from_channel_with_signature(opsdroid):
    response = {
        "update_id": 639974076,
        "channel_post": {
            "message_id": 15,
            "author_signature": "Fabio Rosado",
            "chat": {"id": -1001474700000, "title": "Opsdroid-test", "type": "channel"},
            "date": 1603827365,
            "text": "hi",
        },
    }

    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    user, user_id = connector.get_user(response, "")

    assert user == "Fabio Rosado"
    assert user_id == 15


def test_get_user_from_channel_without_signature(opsdroid):
    response = {
        "update_id": 639974076,
        "channel_post": {
            "message_id": 16,
            "chat": {"id": -1001474700000, "title": "Opsdroid-test", "type": "channel"},
            "date": 1603827365,
            "text": "hi",
        },
    }

    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    user, user_id = connector.get_user(response, "Opsdroid!")

    assert user == "Opsdroid!"
    assert user_id == 16


def test_get_user_from_forwarded_message(opsdroid):
    response = {
        "update_id": 639974077,
        "message": {
            "message_id": 31,
            "from": {"id": 100000, "is_bot": False, "first_name": "Telegram"},
            "chat": {
                "id": -10014170000,
                "title": "Opsdroid-test Chat",
                "type": "supergroup",
            },
            "date": 1603827368,
            "forward_from_chat": {
                "id": -10014740000,
                "title": "Opsdroid-test",
                "type": "channel",
            },
            "forward_from_message_id": 15,
            "forward_signature": "Fabio Rosado",
            "forward_date": 1603827365,
            "text": "hi",
        },
    }

    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    user, user_id = connector.get_user(response, "Opsdroid!")

    assert user == "Fabio Rosado"
    assert user_id == 100000


def test_get_user_from_first_name(opsdroid):
    response = {
        "update_id": 639974077,
        "message": {
            "message_id": 31,
            "from": {"id": 100000, "is_bot": False, "first_name": "Fabio"},
            "chat": {
                "id": -10014170000,
                "title": "Opsdroid-test Chat",
                "type": "supergroup",
            },
            "date": 1603827368,
            "text": "hi",
        },
    }

    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    user, user_id = connector.get_user(response, "")

    assert user == "Fabio"
    assert user_id == 100000


def test_get_user_from_username(opsdroid):
    response = {
        "update_id": 639974077,
        "message": {
            "message_id": 31,
            "from": {"id": 100000, "is_bot": False, "username": "FabioRosado"},
            "chat": {
                "id": -10014170000,
                "title": "Opsdroid-test Chat",
                "type": "supergroup",
            },
            "date": 1603827368,
            "text": "hi",
        },
    }

    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    user, user_id = connector.get_user(response, "")

    assert user == "FabioRosado"
    assert user_id == 100000


def test_handle_user_permission(opsdroid):
    response = {
        "update_id": 639974077,
        "message": {
            "message_id": 31,
            "from": {"id": 100000, "is_bot": False, "username": "FabioRosado"},
            "chat": {
                "id": -10014170000,
                "title": "Opsdroid-test Chat",
                "type": "supergroup",
            },
            "date": 1603827368,
            "text": "hi",
        },
    }

    connector_config["whitelisted-users"] = ["FabioRosado"]

    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    permission = connector.handle_user_permission(response, "FabioRosado", 100000)

    assert permission is True


def test_handle_user_id_permission(opsdroid):
    response = {
        "update_id": 639974077,
        "message": {
            "message_id": 31,
            "from": {"id": 100000, "is_bot": False, "username": "FabioRosado"},
            "chat": {
                "id": -10014170000,
                "title": "Opsdroid-test Chat",
                "type": "supergroup",
            },
            "date": 1603827368,
            "text": "hi",
        },
    }

    connector_config["whitelisted-users"] = [100000]

    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    permission = connector.handle_user_permission(response, "FabioRosado", 100000)

    assert permission is True


def test_handle_user_no_permission(opsdroid):
    response = {
        "update_id": 639974077,
        "message": {
            "message_id": 31,
            "from": {"id": 100000, "is_bot": False, "username": "FabioRosado"},
            "chat": {
                "id": -10014170000,
                "title": "Opsdroid-test Chat",
                "type": "supergroup",
            },
            "date": 1603827368,
            "text": "hi",
        },
    }

    connector_config["whitelisted-users"] = [1, "AllowedUser"]

    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    permission = connector.handle_user_permission(response, "FabioRosado", 100000)

    assert permission is False


def test_build_url(opsdroid):
    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    url = connector.build_url("getUpdates")

    assert url == "https://api.telegram.org/bottest:token/getUpdates"


@pytest.mark.asyncio
async def test_connect(opsdroid):

    opsdroid.config["web"] = {"base-url": "https://test.com"}
    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    connector.webhook_secret = "test_secret"

    opsdroid.web_server = amock.Mock()
    response = amock.Mock()
    response.status = 200

    with amock.patch(
        "aiohttp.ClientSession.post", new=amock.CoroutineMock()
    ) as patched_request, amock.patch.object(
        connector, "build_url"
    ) as mocked_build_url:
        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(response)

        await connector.connect()

        assert opsdroid.web_server.web_app.router.add_post.called
        assert patched_request is not None
        assert mocked_build_url.called


@pytest.mark.asyncio
async def test_connect_failure(opsdroid, caplog):
    caplog.set_level(logging.ERROR)

    opsdroid.config["web"] = {"base-url": "https://test.com"}
    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    connector.webhook_secret = "test_secret"

    opsdroid.web_server = amock.Mock()
    response = amock.Mock()

    response.status = 404

    with amock.patch(
        "aiohttp.ClientSession.post", new=amock.CoroutineMock()
    ) as patched_request, amock.patch.object(
        connector, "build_url"
    ) as mocked_build_url:
        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(response)

        await connector.connect()

        assert opsdroid.web_server.web_app.router.add_post.called
        assert patched_request is not None
        assert mocked_build_url.called
        assert "Error when connecting to Telegram" in caplog.text


@pytest.mark.asyncio
async def test_respond(opsdroid, caplog):
    caplog.set_level(logging.DEBUG)

    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    response = amock.Mock()
    response.status = 200

    with amock.patch(
        "aiohttp.ClientSession.post", new=amock.CoroutineMock()
    ) as patched_request, amock.patch.object(
        connector, "build_url"
    ) as mocked_build_url:
        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(response)

        assert opsdroid.__class__.instances

        test_message = Message(
            text="This is a test",
            user="opsdroid",
            target={"id": 12404},
            connector=connector,
        )

        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(response)

        await test_message.respond("Response")

        assert patched_request.called
        assert mocked_build_url.called
        assert "Responding" in caplog.text
        assert "Successfully responded" in caplog.text


@pytest.mark.asyncio
async def test_respond_failure(opsdroid, caplog):
    caplog.set_level(logging.DEBUG)

    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    response = amock.Mock()
    response.status = 500

    with amock.patch(
        "aiohttp.ClientSession.post", new=amock.CoroutineMock()
    ) as patched_request, amock.patch.object(
        connector, "build_url"
    ) as mocked_build_url:
        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(response)

        assert opsdroid.__class__.instances

        test_message = Message(
            text="This is a test",
            user="opsdroid",
            target={"id": 12404},
            connector=connector,
        )

        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(response)

        await test_message.respond("Response")

        assert patched_request.called
        assert mocked_build_url.called
        assert "Responding" in caplog.text
        assert "Unable to respond" in caplog.text


@pytest.mark.asyncio
async def test_respond_image(opsdroid, caplog):
    caplog.set_level(logging.DEBUG)

    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    post_response = amock.Mock()
    post_response.status = 200

    gif_bytes = (
        b"GIF89a\x01\x00\x01\x00\x00\xff\x00,"
        b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;"
    )

    image = Image(file_bytes=gif_bytes, target={"id": "123"})

    with amock.patch(
        "aiohttp.ClientSession.post", new=amock.CoroutineMock()
    ) as patched_request, amock.patch.object(
        connector, "build_url"
    ) as mocked_build_url:

        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(post_response)

        await connector.send_image(image)

        assert mocked_build_url.called
        assert patched_request.called
        assert "Sent" in caplog.text


@pytest.mark.asyncio
async def test_respond_image_failure(opsdroid, caplog):
    caplog.set_level(logging.DEBUG)

    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    post_response = amock.Mock()
    post_response.status = 400

    gif_bytes = (
        b"GIF89a\x01\x00\x01\x00\x00\xff\x00,"
        b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;"
    )

    image = Image(file_bytes=gif_bytes, target={"id": "123"})

    with amock.patch(
        "aiohttp.ClientSession.post", new=amock.CoroutineMock()
    ) as patched_request, amock.patch.object(
        connector, "build_url"
    ) as mocked_build_url:

        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(post_response)

        await connector.send_image(image)

        assert mocked_build_url.called
        assert patched_request.called
        assert "Unable to send image" in caplog.text


@pytest.mark.asyncio
async def test_respond_file(opsdroid, caplog):
    caplog.set_level(logging.DEBUG)

    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    post_response = amock.Mock()
    post_response.status = 200

    file_bytes = b"plain text file example"

    file = File(file_bytes=file_bytes, target={"id": "123"})

    with amock.patch(
        "aiohttp.ClientSession.post", new=amock.CoroutineMock()
    ) as patched_request, amock.patch.object(
        connector, "build_url"
    ) as mocked_build_url:

        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(post_response)

        await connector.send_file(file)

        assert mocked_build_url.called
        assert patched_request.called
        assert "Sent" in caplog.text


async def test_respond_file_failure(opsdroid, caplog):
    caplog.set_level(logging.DEBUG)

    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    post_response = amock.Mock()
    post_response.status = 400

    file_bytes = b"plain text file example"

    file = File(file_bytes=file_bytes, target={"id": "123"})

    with amock.patch(
        "aiohttp.ClientSession.post", new=amock.CoroutineMock()
    ) as patched_request, amock.patch.object(
        connector, "build_url"
    ) as mocked_build_url:

        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(post_response)

        await connector.send_file(file)

        assert mocked_build_url.called
        assert patched_request.called
        assert "Unable to send file" in caplog.text


async def test_disconnect_successful(opsdroid, caplog):
    caplog.set_level(logging.DEBUG)

    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    response = amock.Mock()
    response.status = 200

    with amock.patch(
        "aiohttp.ClientSession.get", new=amock.CoroutineMock()
    ) as patched_request, amock.patch.object(
        connector, "build_url"
    ) as mocked_build_url:

        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(response)

        await connector.disconnect()

        assert mocked_build_url.called
        assert patched_request.called
        assert "Sending deleteWebhook" in caplog.text
        assert "Telegram webhook deleted" in caplog.text


async def test_disconnect_failure(opsdroid, caplog):
    caplog.set_level(logging.DEBUG)

    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    response = amock.Mock()
    response.status = 400

    with amock.patch(
        "aiohttp.ClientSession.get", new=amock.CoroutineMock()
    ) as patched_request, amock.patch.object(
        connector, "build_url"
    ) as mocked_build_url:

        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(response)

        await connector.disconnect()

        assert mocked_build_url.called
        assert patched_request.called
        assert "Sending deleteWebhook" in caplog.text
        assert "Unable to delete webhook" in caplog.text


# class TestConnectorTelegramAsync(asynctest.TestCase):
#     """Test the async methods of the opsdroid Telegram connector class."""

#     def setUp(self):
#         configure_lang({})
#         self.connector = ConnectorTelegram(
#             {
#                 "name": "telegram",
#                 "token": "bot:765test",
#                 "whitelisted-users": ["user", "test", "AnUser"],
#             },
#             opsdroid=OpsDroid(),
#         )
#         with amock.patch("aiohttp.ClientSession") as mocked_session:
#             self.connector.session = mocked_session

#     async def test_connect(self):
#         connect_response = amock.Mock()
#         connect_response.status = 200
#         connect_response.json = amock.CoroutineMock()
#         connect_response.return_value = {
#             "ok": True,
#             "result": {
#                 "id": 635392558,
#                 "is_bot": True,
#                 "first_name": "opsdroid",
#                 "username": "opsdroid_bot",
#             },
#         }

#         with amock.patch("aiohttp.ClientSession.get") as patched_request:

#             patched_request.return_value = asyncio.Future()
#             patched_request.return_value.set_result(connect_response)
#             await self.connector.connect()
#             self.assertLogs("_LOGGER", "debug")
#             self.assertNotEqual(200, patched_request.status)
#             self.assertTrue(patched_request.called)

#     async def test_connect_failure(self):
#         result = amock.MagicMock()
#         result.status = 401

#         with amock.patch("aiohttp.ClientSession.get") as patched_request:

#             patched_request.return_value = asyncio.Future()
#             patched_request.return_value.set_result(result)

#             await self.connector.connect()
#             self.assertLogs("_LOGGER", "error")

#     async def test_parse_message_username(self):
#         response = {
#             "result": [
#                 {
#                     "update_id": 427647860,
#                     "message": {
#                         "message_id": 12,
#                         "from": {
#                             "id": 649671308,
#                             "is_bot": False,
#                             "first_name": "A",
#                             "last_name": "User",
#                             "username": "user",
#                             "language_code": "en-GB",
#                         },
#                         "chat": {
#                             "id": 649671308,
#                             "first_name": "A",
#                             "last_name": "User",
#                             "username": "user",
#                             "type": "private",
#                         },
#                         "date": 1538756863,
#                         "text": "Hello",
#                     },
#                 }
#             ]
#         }

#         with amock.patch("opsdroid.core.OpsDroid.parse") as mocked_parse:
#             await self.connector._parse_message(response)
#             self.assertTrue(mocked_parse.called)

#     async def test_parse_edited_message(self):
#         response = {
#             "result": [
#                 {
#                     "update_id": 246644499,
#                     "edited_message": {
#                         "message_id": 150,
#                         "from": {
#                             "id": 245245245,
#                             "is_bot": False,
#                             "first_name": "IOBreaker",
#                             "language_code": "en",
#                         },
#                         "chat": {
#                             "id": 245245245,
#                             "first_name": "IOBreaker",
#                             "type": "private",
#                         },
#                         "date": 1551797346,
#                         "edit_date": 1551797365,
#                         "text": "hello2",
#                     },
#                 }
#             ]
#         }
#         mocked_status = amock.CoroutineMock()
#         mocked_status.status = 200
#         with amock.patch("opsdroid.core.OpsDroid.parse"), amock.patch.object(
#             self.connector, "get_messages_loop"
#         ), amock.patch.object(self.connector.session, "post") as patched_request:
#             patched_request.return_value = asyncio.Future()
#             patched_request.return_value.set_result(mocked_status)
#             self.assertTrue(response["result"][0].get("edited_message"))
#             await self.connector._parse_message(response)

#     async def test_parse_message_channel(self):
#         response = {
#             "result": [
#                 {
#                     "update_id": 427647860,
#                     "message": {
#                         "message_id": 12,
#                         "from": {
#                             "id": 649671308,
#                             "is_bot": False,
#                             "first_name": "A",
#                             "last_name": "User",
#                             "username": "user",
#                             "language_code": "en-GB",
#                         },
#                         "chat": {
#                             "id": 649671308,
#                             "first_name": "A",
#                             "last_name": "User",
#                             "username": "user",
#                             "type": "channel",
#                         },
#                         "date": 1538756863,
#                         "text": "Hello",
#                     },
#                 }
#             ]
#         }

#         with amock.patch("opsdroid.core.OpsDroid.parse"):
#             await self.connector._parse_message(response)
#             self.assertLogs("_LOGGER", "debug")

#     async def test_parse_message_first_name(self):
#         response = {
#             "result": [
#                 {
#                     "update_id": 427647860,
#                     "message": {
#                         "message_id": 12,
#                         "from": {
#                             "id": 649671308,
#                             "is_bot": Falsei,
#                             "first_name": "AnUser",
#                             "type": "private",
#                             "language_code": "en-GB",
#                         },
#                         "chat": {
#                             "id": 649671308,
#                             "first_name": "AnUser",
#                             "type": "private",
#                         },
#                         "date": 1538756863,
#                         "text": "Hello",
#                     },
#                 }
#             ]
#         }
#         with amock.patch("opsdroid.core.OpsDroid.parse") as mocked_parse:
#             await self.connector._parse_message(response)
#             self.assertTrue(mocked_parse.called)

#     async def test_parse_message_bad_result(self):
#         response = {
#             "result": [
#                 {
#                     "update_id": 427647860,
#                     "message": {
#                         "message_id": 12,
#                         "from": {
#                             "id": 649671308,
#                             "is_bot": False,
#                             "first_name": "test",
#                             "language_code": "en-GB",
#                         },
#                         "chat": {
#                             "id": 649671308,
#                             "first_name": "test",
#                             "type": "private",
#                         },
#                         "date": 1538756863,
#                     },
#                 }
#             ]
#         }

#         await self.connector._parse_message(response)
#         self.assertLogs("error", "_LOGGER")

#     async def test_parse_message_unauthorized(self):
#         self.connector.config["whitelisted-users"] = ["user", "test"]
#         response = {
#             "result": [
#                 {
#                     "update_id": 427647860,
#                     "message": {
#                         "message_id": 12,
#                         "from": {
#                             "id": 649671308,
#                             "is_bot": False,
#                             "first_name": "A",
#                             "last_name": "User",
#                             "username": "a_user",
#                             "language_code": "en-GB",
#                         },
#                         "chat": {
#                             "id": 649671308,
#                             "first_name": "A",
#                             "last_name": "User",
#                             "username": "a_user",
#                             "type": "private",
#                         },
#                         "date": 1538756863,
#                         "text": "Hello",
#                     },
#                 }
#             ]
#         }

#         self.assertEqual(self.connector.config["whitelisted-users"], ["user", "test"])

#         message_text = "Sorry, you're not allowed to speak with this bot."

#         with amock.patch.object(self.connector, "send") as mocked_respond:
#             await self.connector._parse_message(response)
#             self.assertTrue(mocked_respond.called)
#             self.assertTrue(mocked_respond.called_with(message_text))

#     async def test_parse_message_emoji(self):
#         response = {
#             "result": [
#                 {
#                     "update_id": 427647860,
#                     "message": {
#                         "message_id": 12,
#                         "from": {
#                             "id": 649671308,
#                             "is_bot": False,
#                             "first_name": "A",
#                             "last_name": "User",
#                             "username": "user",
#                             "language_code": "en-GB",
#                         },
#                         "chat": {
#                             "id": 649671308,
#                             "first_name": "A",
#                             "last_name": "User",
#                             "username": "user",
#                             "type": "private",
#                         },
#                         "date": 1538756863,
#                         "sticker": {
#                             "width": 512,
#                             "height": 512,
#                             "emoji": "😔",
#                             "set_name": "YourALF",
#                             "thumb": {
#                                 "file_id": "AAQCABODB_MOAARYC8yRaPPoIIZBAAIC",
#                                 "file_size": 8582,
#                                 "width": 128,
#                                 "height": 128,
#                             },
#                             "file_id": "CAADAgAD3QMAAsSraAu37DAtdiNpAgI",
#                             "file_size": 64720,
#                         },
#                     },
#                 }
#             ]
#         }

#         with amock.patch("opsdroid.core.OpsDroid.parse"):
#             await self.connector._parse_message(response)
#             self.assertLogs("_LOGGER", "debug")

#     async def test_get_messages(self):
#         listen_response = amock.Mock()
#         listen_response.status = 200
#         listen_response.json = amock.CoroutineMock()
#         listen_response.return_value = {
#             "result": [
#                 {
#                     "update_id": 427647860,
#                     "message": {
#                         "message_id": 54,
#                         "from": {
#                             "id": 639889348,
#                             "is_bot": False,
#                             "first_name": "Fabio",
#                             "last_name": "Rosado",
#                             "username": "FabioRosado",
#                             "language_code": "en-GB",
#                         },
#                         "chat": {
#                             "id": 639889348,
#                             "first_name": "Fabio",
#                             "last_name": "Rosado",
#                             "username": "FabioRosado",
#                             "type": "private",
#                         },
#                         "date": 1538756863,
#                         "text": "Hello",
#                     },
#                 }
#             ]
#         }

#         with amock.patch.object(
#             self.connector.session, "get"
#         ) as patched_request, amock.patch.object(
#             self.connector, "_parse_message"
#         ) as mocked_parse_message:

#             self.connector.latest_update = 54

#             patched_request.return_value = asyncio.Future()
#             patched_request.return_value.set_result(listen_response)
#             await self.connector._get_messages()
#             self.assertTrue(patched_request.called)
#             self.assertLogs("_LOGGER", "debug")
#             self.assertTrue(mocked_parse_message.called)

#     async def test_delete_webhook(self):
#         response = amock.Mock()
#         response.status = 200

#         with amock.patch.object(self.connector.session, "get") as mock_request:
#             mock_request.return_value = asyncio.Future()
#             mock_request.return_value.set_result(response)

#             await self.connector.delete_webhook()
#             self.assertLogs("_LOGGER", "debug")

#     async def test_get_message_webhook(self):
#         response = amock.Mock()
#         response.status = 409

#         with amock.patch.object(
#             self.connector.session, "get"
#         ) as mock_request, amock.patch.object(
#             self.connector, "delete_webhook"
#         ) as mock_method:
#             mock_request.return_value = asyncio.Future()
#             mock_request.return_value.set_result(response)

#             await self.connector._get_messages()
#             self.assertLogs("_LOGGER", "info")
#             self.assertTrue(mock_method.called)

#     async def test_delete_webhook_failure(self):
#         response = amock.Mock()
#         response.status = 401

#         with amock.patch.object(self.connector.session, "get") as mock_request:
#             mock_request.return_value = asyncio.Future()
#             mock_request.return_value.set_result(response)

#             await self.connector.delete_webhook()
#             self.assertLogs("_LOGGER", "debug")

#     async def test_get_messages_failure(self):
#         listen_response = amock.Mock()
#         listen_response.status = 401

#         with amock.patch.object(self.connector.session, "get") as patched_request:

#             patched_request.return_value = asyncio.Future()
#             patched_request.return_value.set_result(listen_response)
#             await self.connector._get_messages()
#             self.assertLogs("_LOGGER", "error")

#     async def test_get_messages_loop(self):
#         self.connector._get_messages = amock.CoroutineMock()
#         self.connector._get_messages.side_effect = Exception()
#         with contextlib.suppress(Exception):
#             await self.connector.get_messages_loop()


#     async def test_respond_failure(self):
#         post_response = amock.Mock()
#         post_response.status = 401

#         with OpsDroid() as opsdroid, amock.patch.object(
#             self.connector.session, "post"
#         ) as patched_request:

#             self.assertTrue(opsdroid.__class__.instances)
#             test_message = Message(
#                 text="This is a test",
#                 user="opsdroid",
#                 target={"id": 12404},
#                 connector=self.connector,
#             )

#             patched_request.return_value = asyncio.Future()
#             patched_request.return_value.set_result(post_response)
#             await test_message.respond("Response")
#             self.assertLogs("_LOGGER", "debug")


#     async def test_listen(self):
#         with amock.patch.object(
#             self.connector.loop, "create_task"
#         ) as mocked_task, amock.patch.object(
#             self.connector._closing, "wait"
#         ) as mocked_event, amock.patch.object(
#             self.connector, "get_messages_loop"
#         ):
#             mocked_event.return_value = asyncio.Future()
#             mocked_event.return_value.set_result(True)
#             mocked_task.return_value = asyncio.Future()
#             await self.connector.listen()

#             self.assertTrue(mocked_event.called)
#             self.assertTrue(mocked_task.called)

#     async def test_disconnect(self):
#         with amock.patch.object(self.connector.session, "close") as mocked_close:
#             mocked_close.return_value = asyncio.Future()
#             mocked_close.return_value.set_result(True)

#             await self.connector.disconnect()
#             self.assertFalse(self.connector.listening)
#             self.assertTrue(self.connector.session.closed())
#             self.assertEqual(self.connector._closing.set(), None)
