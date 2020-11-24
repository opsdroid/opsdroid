import logging
import asyncio
import pytest
import asynctest.mock as amock


from opsdroid.connector.telegram import ConnectorTelegram

import opsdroid.connector.telegram.events as telegram_events
import opsdroid.events as opsdroid_events


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
    assert "Breaking changes introduced" in caplog.text


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

        test_message = opsdroid_events.Message(
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

        test_message = opsdroid_events.Message(
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

    image = opsdroid_events.Image(file_bytes=gif_bytes, target={"id": "123"})

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

    image = opsdroid_events.Image(file_bytes=gif_bytes, target={"id": "123"})

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

    file = opsdroid_events.File(file_bytes=file_bytes, target={"id": "123"})

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

    file = opsdroid_events.File(file_bytes=file_bytes, target={"id": "123"})

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


@pytest.mark.asyncio
async def test_edited_message_event(opsdroid):
    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    mock_request = amock.CoroutineMock()
    mock_request.json = amock.CoroutineMock()
    mock_request.json.return_value = {
        "update_id": 639974040,
        "edited_message": {
            "message_id": 1247,
            "from": {
                "id": 6399348,
                "is_bot": False,
                "first_name": "Fabio",
                "last_name": "Rosado",
                "username": "FabioRosado",
                "language_code": "en",
            },
            "chat": {
                "id": 6399348,
                "first_name": "Fabio",
                "last_name": "Rosado",
                "username": "FabioRosado",
                "type": "private",
            },
            "date": 1603818326,
            "edit_date": 1603818330,
            "text": "hi",
        },
    }

    edited_message = opsdroid_events.EditedMessage("hi", 6399348, "Fabio", 6399348)

    await connector.telegram_webhook_handler(mock_request)

    assert "hi" in edited_message.text
    assert "Fabio" in edited_message.user
    assert edited_message.target == 6399348
    assert edited_message.user_id == 6399348


@pytest.mark.asyncio
async def test_join_group_event(opsdroid):
    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    mock_request = amock.CoroutineMock()
    mock_request.json = amock.CoroutineMock()
    mock_request.json.return_value = {
        "update_id": 639974040,
        "message": {
            "message_id": 1247,
            "from": {
                "id": 6399348,
                "is_bot": False,
                "first_name": "Fabio",
                "last_name": "Rosado",
                "username": "FabioRosado",
                "language_code": "en",
            },
            "chat": {
                "id": 6399348,
                "first_name": "Fabio",
                "last_name": "Rosado",
                "username": "FabioRosado",
                "type": "private",
            },
            "date": 1603818326,
            "edit_date": 1603818330,
            "new_chat_member": True,
        },
    }

    join_message = opsdroid_events.JoinGroup(6399348, "Fabio", 6399348)

    await connector.telegram_webhook_handler(mock_request)

    assert "Fabio" in join_message.user
    assert join_message.target == 6399348
    assert join_message.user_id == 6399348


@pytest.mark.asyncio
async def test_leave_group_event(opsdroid):
    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    mock_request = amock.CoroutineMock()
    mock_request.json = amock.CoroutineMock()
    mock_request.json.return_value = {
        "update_id": 639974040,
        "message": {
            "message_id": 1247,
            "from": {
                "id": 6399348,
                "is_bot": False,
                "first_name": "Fabio",
                "last_name": "Rosado",
                "username": "FabioRosado",
                "language_code": "en",
            },
            "chat": {
                "id": 6399348,
                "first_name": "Fabio",
                "last_name": "Rosado",
                "username": "FabioRosado",
                "type": "private",
            },
            "date": 1603818326,
            "edit_date": 1603818330,
            "left_chat_member": True,
        },
    }

    left_message = opsdroid_events.LeaveGroup(6399348, "Fabio", 6399348)

    await connector.telegram_webhook_handler(mock_request)

    assert "Fabio" in left_message.user
    assert left_message.target == 6399348
    assert left_message.user_id == 6399348


@pytest.mark.asyncio
async def test_pinned_message_event(opsdroid):
    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    mock_request = amock.CoroutineMock()
    mock_request.json = amock.CoroutineMock()
    mock_request.json.return_value = {
        "update_id": 639974040,
        "message": {
            "message_id": 1247,
            "from": {
                "id": 6399348,
                "is_bot": False,
                "first_name": "Fabio",
                "last_name": "Rosado",
                "username": "FabioRosado",
                "language_code": "en",
            },
            "chat": {
                "id": 6399348,
                "first_name": "Fabio",
                "last_name": "Rosado",
                "username": "FabioRosado",
                "type": "private",
            },
            "date": 1603818326,
            "edit_date": 1603818330,
            "pinned_message": True,
        },
    }

    pinned_message = opsdroid_events.PinMessage(6399348, "Fabio", 6399348)

    await connector.telegram_webhook_handler(mock_request)

    assert "Fabio" in pinned_message.user
    assert pinned_message.target == 6399348
    assert pinned_message.user_id == 6399348


@pytest.mark.asyncio
async def test_reply_to_message_event(opsdroid):
    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    mock_request = amock.CoroutineMock()
    mock_request.json = amock.CoroutineMock()
    mock_request.json.return_value = {
        "update_id": 639974084,
        "message": {
            "message_id": 1272,
            "from": {
                "id": 639348,
                "is_bot": False,
                "first_name": "Fabio",
                "last_name": "Rosado",
                "username": "FabioRosado",
                "language_code": "en",
            },
            "chat": {
                "id": 639348,
                "first_name": "Fabio",
                "last_name": "Rosado",
                "username": "FabioRosado",
                "type": "private",
            },
            "date": 1603834922,
            "reply_to_message": {
                "message_id": 1271,
                "from": {
                    "id": 639348,
                    "is_bot": False,
                    "first_name": "Fabio",
                    "last_name": "Rosado",
                    "username": "FabioRosado",
                    "language_code": "en",
                },
                "chat": {
                    "id": 63948,
                    "first_name": "Fabio",
                    "last_name": "Rosado",
                    "username": "FabioRosado",
                    "type": "private",
                },
                "date": 1603834912,
                "text": "Hi",
            },
            "text": "This is a reply",
        },
    }

    reply_message = opsdroid_events.Reply(
        "This is a reply", 639348, "FabioRosado", 63948
    )

    await connector.telegram_webhook_handler(mock_request)

    assert "This is a reply" in reply_message.text
    assert "FabioRosado" in reply_message.user
    assert reply_message.target == 63948


@pytest.mark.asyncio
async def test_location_event(opsdroid):
    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    mock_request = amock.CoroutineMock()
    mock_request.json = amock.CoroutineMock()
    mock_request.json.return_value = {
        "update_id": 639974101,
        "message": {
            "message_id": 42,
            "from": {
                "id": 1087968824,
                "is_bot": True,
                "first_name": "Group",
                "username": "GroupAnonymousBot",
            },
            "chat": {
                "id": -1001417735217,
                "title": "Opsdroid-test Chat",
                "type": "supergroup",
            },
            "date": 1603992829,
            "location": {"latitude": 56.159849, "longitude": -5.230604},
        },
    }

    event_location = telegram_events.Location(
        {"location": {"latitude": 56.159849, "longitude": -5.230604}},
        56.159849,
        -5.230604,
    )

    await connector.telegram_webhook_handler(mock_request)

    assert event_location.latitude == 56.159849
    assert event_location.longitude == -5.230604


@pytest.mark.asyncio
async def test_poll_event(opsdroid):
    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    mock_request = amock.CoroutineMock()
    mock_request.json = amock.CoroutineMock()
    mock_request.json.return_value = {
        "update_id": 639974103,
        "message": {
            "message_id": 44,
            "from": {
                "id": 1087968824,
                "is_bot": True,
                "first_name": "Group",
                "username": "GroupAnonymousBot",
            },
            "chat": {
                "id": -1001417735217,
                "title": "Opsdroid-test Chat",
                "type": "supergroup",
            },
            "date": 1603993170,
            "poll": {
                "id": "5825895662671101957",
                "question": "Test",
                "options": [
                    {"text": "Test", "voter_count": 0},
                    {"text": "Testing", "voter_count": 0},
                ],
                "total_voter_count": 0,
                "is_closed": False,
                "is_anonymous": True,
                "type": "regular",
                "allows_multiple_answers": False,
            },
        },
    }

    poll_event = telegram_events.Poll(
        {
            "question": "question",
            "option": ["option1", "option2"],
            "total_voter_count": 1,
        },
        "question",
        ["option1", "option2"],
        1,
    )

    await connector.telegram_webhook_handler(mock_request)

    assert poll_event.question == "question"
    assert poll_event.options == ["option1", "option2"]
    assert poll_event.total_votes == 1


@pytest.mark.asyncio
async def test_contact_event(opsdroid):
    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    mock_request = amock.CoroutineMock()
    mock_request.json = amock.CoroutineMock()
    mock_request.json.return_value = {
        "update_id": 1,
        "message": {
            "chat": {"id": 321},
            "from": {"id": 123},
            "contact": {"phone_number": 123456, "first_name": "opsdroid"},
        },
    }

    contact_event = telegram_events.Contact(
        {"phone_number": 123456, "first_name": "opsdroid"}, 123456, "opsdroid"
    )

    await connector.telegram_webhook_handler(mock_request)

    assert contact_event.first_name == "opsdroid"
    assert contact_event.phone_number == 123456


@pytest.mark.asyncio
async def test_unparseable_event(opsdroid, caplog):
    caplog.set_level(logging.DEBUG)

    opsdroid.config["web"] = {"base-url": "https://test.com"}

    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    message = {
        "update_id": 1,
        "message": {
            "message_id": 1279,
            "from": {
                "id": 639889348,
                "is_bot": False,
                "first_name": "Fabio",
                "last_name": "Rosado",
                "username": "FabioRosado",
                "language_code": "en",
            },
            "chat": {
                "id": 639889348,
                "first_name": "Fabio",
                "last_name": "Rosado",
                "username": "FabioRosado",
                "type": "private",
            },
            "date": 1604013500,
            "sticker": {
                "width": 512,
                "height": 512,
                "emoji": "👌",
                "set_name": "HotCherry",
                "is_animated": True,
                "file_size": 42311,
            },
        },
    }
    event = await connector.handle_messages(message, "opsdroid", 0, 1)

    assert "Received unparsable event" in caplog.text
    assert event is None


@pytest.mark.asyncio
async def test_channel_post(opsdroid):
    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    mock_request = amock.CoroutineMock()
    mock_request.json = amock.CoroutineMock()
    mock_request.json.return_value = {
        "update_id": 639974037,
        "channel_post": {
            "message_id": 4,
            "chat": {"id": -1001474709998, "title": "Opsdroid-test", "type": "channel"},
            "date": 1603817533,
            "text": "dance",
        },
    }

    message = opsdroid_events.Message("dance", 4, opsdroid)
    await connector.telegram_webhook_handler(mock_request)

    assert message.text == "dance"


@pytest.mark.asyncio
async def test_parse_user_no_permissions(opsdroid):
    mock_request = amock.CoroutineMock()
    mock_request.json = amock.CoroutineMock()
    mock_request.json.return_value = {
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
    connector_config["reply-unauthorized"] = True

    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    with amock.patch.object(connector, "send_message") as mocked_send_message:

        await connector.telegram_webhook_handler(mock_request)

        assert mocked_send_message.called


@pytest.mark.asyncio
async def test_parse_user_permissions(opsdroid):
    mock_request = amock.CoroutineMock()
    mock_request.json = amock.CoroutineMock()
    mock_request.json.return_value = {
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

    connector_config["whitelisted-users"] = ["FabioRosado", 100000]

    connector = ConnectorTelegram(connector_config, opsdroid=opsdroid)

    with amock.patch.object(connector.opsdroid, "parse") as mocked_parse:

        await connector.telegram_webhook_handler(mock_request)

        assert mocked_parse.called
