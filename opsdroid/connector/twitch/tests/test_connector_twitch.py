import os
import logging
import contextlib
import asyncio
import pytest
import asynctest.mock as amock

from aiohttp import web, WSMessage, WSMsgType
from aiohttp.test_utils import make_mocked_request

from opsdroid.connector.twitch import ConnectorTwitch
import opsdroid.events as opsdroid_events
import opsdroid.connector.twitch.events as twitch_event


AUTH_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "twitch.json")

connector_config = {
    "code": "yourcode",
    "channel": "test",
    "client-id": "client-id",
    "client-secret": "client-secret",
}


def test_init(opsdroid):
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)
    assert connector.default_target == "test"
    assert connector.name == "twitch"
    assert connector.token is None
    assert connector.websocket is None
    assert connector.user_id is None
    assert connector.reconnections == 0


def test_base_url_twitch_config(opsdroid):
    config = {
        "code": "yourcode",
        "channel": "test",
        "client-id": "client-id",
        "client-secret": "client-secret",
        "forward-url": "http://my-awesome-url",
    }

    connector = ConnectorTwitch(config, opsdroid=opsdroid)

    assert connector.base_url == "http://my-awesome-url"


def test_base_url_web_config(opsdroid):
    config = {
        "code": "yourcode",
        "channel": "test",
        "client-id": "client-id",
        "client-secret": "client-secret",
    }

    opsdroid.config["web"] = {"base-url": "http://my-awesome-url"}

    connector = ConnectorTwitch(config, opsdroid=opsdroid)

    assert connector.base_url == "http://my-awesome-url"


@pytest.mark.asyncio
async def test_validate_request(opsdroid):
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)
    request = amock.CoroutineMock()
    request.headers = {
        "x-hub-signature": "sha256=fcfa24b327e3467f1586cc1ace043c016cabfe9c15dabc0020aca45440338be9"
    }

    request.read = amock.CoroutineMock()
    request.read.return_value = b'{"test": "test"}'

    validation = await connector.validate_request(request, "test")

    assert validation


@pytest.mark.asyncio
async def test_get_user_id(opsdroid):
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)
    get_response = amock.Mock()
    get_response.status = 200
    get_response.json = amock.CoroutineMock()
    get_response.json.return_value = {"data": [{"id": "test-bot"}]}

    with amock.patch(
        "aiohttp.ClientSession.get", new=amock.CoroutineMock()
    ) as patched_request:
        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(get_response)

        response = await connector.get_user_id("theflyingdev", "token", "client-id")

        assert response == "test-bot"


@pytest.mark.asyncio
async def test_get_user_id_failure(opsdroid, caplog):
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)
    get_response = amock.Mock()
    get_response.status = 404
    get_response.json = amock.CoroutineMock()

    with amock.patch(
        "aiohttp.ClientSession.get", new=amock.CoroutineMock()
    ) as patched_request:
        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(get_response)

        await connector.get_user_id("theflyingdev", "token", "client-id")

        assert "Unable to receive broadcaster id - Error" in caplog.text


@pytest.mark.asyncio
async def test_get_user_id_unauthorized(opsdroid):
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)
    get_response = amock.Mock()
    get_response.status = 401

    with amock.patch(
        "aiohttp.ClientSession.get", new=amock.CoroutineMock()
    ) as patched_request:
        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(get_response)

        with pytest.raises(ConnectionError) as exception:
            await connector.get_user_id("theflyingdev", "token", "client-id")
            assert "Unauthorized" in exception.message


def test_save_authentication_data(opsdroid, tmpdir):
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)
    connector.auth_file = AUTH_FILE

    connector.save_authentication_data(
        {"access_token": "token123", "refresh_token": "refresh_token123"}
    )

    details = connector.get_authorization_data()

    assert details == {"access_token": "token123", "refresh_token": "refresh_token123"}


@pytest.mark.asyncio
async def test_request_oauth_token(opsdroid, tmpdir):
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)
    connector.auth_file = AUTH_FILE

    post_response = amock.Mock()
    post_response.status = 200
    post_response.json = amock.CoroutineMock()
    post_response.json.return_value = {
        "access_token": "token",
        "refresh_token": "refresh_token",
    }

    with amock.patch(
        "aiohttp.ClientSession.post", new=amock.CoroutineMock()
    ) as patched_request:
        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(post_response)

        connector.save_authentication_data = amock.CoroutineMock()

        await connector.request_oauth_token()

        assert connector.token is not None
        assert connector.token == "token"
        assert connector.save_authentication_data.called


@pytest.mark.asyncio
async def test_request_oauth_token_failure(opsdroid, caplog):
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)

    post_response = amock.Mock()
    post_response.status = 400
    post_response.json = amock.CoroutineMock()
    post_response.json.return_value = {
        "status": 400,
        "message": "Parameter redirect_uri does not match registered URI",
    }

    with amock.patch(
        "aiohttp.ClientSession.post", new=amock.CoroutineMock()
    ) as patched_request:
        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(post_response)

        await connector.request_oauth_token()

        assert connector.token is None
        assert "Unable to request oauth token" in caplog.text
        assert "Parameter redirect_uri does not match registered URI" in caplog.text


@pytest.mark.asyncio
async def test_refresh_oauth_token(opsdroid):
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)
    connector.auth_file = AUTH_FILE

    post_response = amock.Mock()
    post_response.status = 200
    post_response.json = amock.CoroutineMock()
    post_response.json.return_value = {
        "access_token": "token",
        "refresh_token": "refresh_token",
    }

    with amock.patch(
        "aiohttp.ClientSession.post", new=amock.CoroutineMock()
    ) as patched_request:
        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(post_response)

        connector.save_authentication_data = amock.CoroutineMock()

        await connector.refresh_token()

        assert connector.token is not None
        assert connector.token == "token"
        assert connector.save_authentication_data.called


@pytest.mark.asyncio
async def test_connect(opsdroid, caplog, tmpdir):
    caplog.set_level(logging.INFO)

    get_response = amock.Mock()
    get_response.status = 200
    get_response.json = amock.CoroutineMock()
    get_response.json.return_value = {"data": [{"id": "test-bot"}]}

    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)
    connector.auth_file = AUTH_FILE
    connector.webhook = amock.CoroutineMock()

    opsdroid.web_server = amock.Mock()

    with amock.patch(
        "aiohttp.ClientSession.get", new=amock.CoroutineMock()
    ) as patched_request:
        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(get_response)

        await connector.connect()

        assert connector.webhook.called
        assert opsdroid.web_server.web_app.router.add_get.called
        assert "Found previous authorization data" in caplog.text


@pytest.mark.asyncio
async def test_connect_no_auth_data(opsdroid, caplog, tmpdir):
    caplog.set_level(logging.INFO)
    get_response = amock.Mock()
    get_response.status = 200
    get_response.json = amock.CoroutineMock()
    get_response.json.return_value = {"data": [{"id": "test-bot"}]}

    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)
    connector.auth_file = AUTH_FILE
    connector.webhook = amock.CoroutineMock()
    connector.request_oauth_token = amock.CoroutineMock()

    opsdroid.web_server = amock.Mock()

    with amock.patch(
        "aiohttp.ClientSession.get", new=amock.CoroutineMock()
    ) as patched_request, amock.patch("os.path") as mocked_file:
        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(get_response)

        mocked_file.isfile = amock.Mock(return_value=False)

        await connector.connect()

        assert "No previous authorization data found" in caplog.text
        assert connector.request_oauth_token.called
        assert opsdroid.web_server.web_app.router.add_get.called
        assert connector.webhook.called


@pytest.mark.asyncio
async def test_connect_refresh_token(opsdroid):
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)
    connector.auth_file = AUTH_FILE
    connector.webhook = amock.CoroutineMock()
    connector.get_user_id = amock.CoroutineMock(side_effect=ConnectionError)
    connector.refresh_token = amock.CoroutineMock()

    opsdroid.web_server = amock.Mock()

    with pytest.raises(ConnectionError):
        await connector.connect()

        assert connector.webhook.called
        assert opsdroid.web_server.web_app.router.add_get.called
        assert connector.refresh_token.called


@pytest.mark.asyncio
async def test_send_message(opsdroid):
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)

    connector.websocket = amock.Mock()
    connector.websocket.send_str = amock.CoroutineMock()

    await connector.send_message("Hello")

    assert connector.websocket.send_str.called


@pytest.mark.asyncio
async def test_send_handshake(opsdroid):
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)

    connector.websocket = amock.Mock()
    connector.websocket.send_str = amock.CoroutineMock()

    await connector.send_handshake()

    assert connector.websocket.send_str.called


@pytest.mark.asyncio
async def test_connect_websocket(opsdroid, caplog):
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)
    caplog.set_level(logging.INFO)

    with amock.patch("aiohttp.ClientSession") as mocked_session:

        mocked_session.ws_connect = amock.CoroutineMock()

        connector.send_handshake = amock.CoroutineMock()
        connector.get_messages_loop = amock.CoroutineMock()

        await connector.connect_websocket()

        assert "Connecting to Twitch IRC Server." in caplog.text
        assert connector.websocket
        assert connector.send_handshake.called
        assert connector.get_messages_loop.called


@pytest.mark.asyncio
async def test_webhook_follows(opsdroid):
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)

    post_response = amock.Mock()
    post_response.status = 200
    post_response.json = amock.CoroutineMock()

    with amock.patch(
        "aiohttp.ClientSession.post", new=amock.CoroutineMock()
    ) as mocked_session:

        mocked_session.return_value = asyncio.Future()
        mocked_session.return_value.set_result(post_response)

        await connector.webhook("follows", "subscribe")

        assert mocked_session.called


@pytest.mark.asyncio
async def test_webhook_stream_changed(opsdroid):
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)

    post_response = amock.Mock()
    post_response.status = 200
    post_response.json = amock.CoroutineMock()

    with amock.patch(
        "aiohttp.ClientSession.post", new=amock.CoroutineMock()
    ) as mocked_session:

        mocked_session.return_value = asyncio.Future()
        mocked_session.return_value.set_result(post_response)

        await connector.webhook("stream changed", "subscribe")

        assert mocked_session.called


@pytest.mark.asyncio
async def test_webhook_subscribers(opsdroid):
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)

    post_response = amock.Mock()
    post_response.status = 200
    post_response.json = amock.CoroutineMock()

    with amock.patch(
        "aiohttp.ClientSession.post", new=amock.CoroutineMock()
    ) as mocked_session:

        mocked_session.return_value = asyncio.Future()
        mocked_session.return_value.set_result(post_response)

        await connector.webhook("subscribers", "subscribe")

        assert mocked_session.called


@pytest.mark.asyncio
async def test_webhook_failure(opsdroid, caplog):
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)

    caplog.set_level(logging.DEBUG)

    post_response = amock.Mock()
    post_response.status = 500
    post_response.json = amock.CoroutineMock()

    with amock.patch(
        "aiohttp.ClientSession.post", new=amock.CoroutineMock()
    ) as mocked_session:

        mocked_session.return_value = asyncio.Future()
        mocked_session.return_value.set_result(post_response)

        await connector.webhook("subscribers", "subscribe")

        assert "Error:" in caplog.text


@pytest.mark.asyncio
async def test_ban_user(opsdroid, caplog):
    caplog.set_level(logging.DEBUG)
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)
    ban_event = opsdroid_events.BanUser(user="bot_mc_spam_bot")

    connector.send_message = amock.CoroutineMock()

    await connector.ban_user(ban_event)

    assert connector.send_message.called
    assert "bot_mc_spam_bot" in caplog.text


@pytest.mark.asyncio
async def test_create_clip(opsdroid, caplog):
    caplog.set_level(logging.DEBUG)
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)
    connector.send_message = amock.CoroutineMock()

    post_response = amock.Mock()
    post_response.status = 200
    post_response.json = amock.CoroutineMock()
    post_response.json.return_value = {"data": [{"id": "clip123"}]}

    get_response = amock.Mock()
    get_response.status = 200
    get_response.json = amock.CoroutineMock()
    get_response.json.return_value = {
        "data": [{"id": "clip123", "embed_url": "localhost"}]
    }

    with amock.patch(
        "aiohttp.ClientSession.post", new=amock.CoroutineMock()
    ) as mocked_post, amock.patch(
        "aiohttp.ClientSession.get", new=amock.CoroutineMock()
    ) as mocked_get:

        mocked_post.return_value = asyncio.Future()
        mocked_post.return_value.set_result(post_response)

        mocked_get.return_value = asyncio.Future()
        mocked_get.return_value.set_result(get_response)

        clip_event = twitch_event.CreateClip(id="broadcaster123")

        await connector.create_clip()

        assert "Twitch clip created successfully." in caplog.text
        assert "broadcaster123" in clip_event.id


@pytest.mark.asyncio
async def test_create_clip_failure(opsdroid, caplog):
    caplog.set_level(logging.DEBUG)
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)
    connector.send_message = amock.CoroutineMock()

    post_response = amock.Mock()
    post_response.status = 200
    post_response.json = amock.CoroutineMock()
    post_response.json.return_value = {"data": [{"id": "clip123"}]}

    get_response = amock.Mock()
    get_response.status = 404

    with amock.patch(
        "aiohttp.ClientSession.post", new=amock.CoroutineMock()
    ) as mocked_post, amock.patch(
        "aiohttp.ClientSession.get", new=amock.CoroutineMock()
    ) as mocked_get:

        mocked_post.return_value = asyncio.Future()
        mocked_post.return_value.set_result(post_response)

        mocked_get.return_value = asyncio.Future()
        mocked_get.return_value.set_result(get_response)

        await connector.create_clip()

        assert "Failed to create Twitch clip" in caplog.text


@pytest.mark.asyncio
async def test_remove_message(opsdroid, caplog):
    caplog.set_level(logging.DEBUG)
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)

    message_event = opsdroid_events.Message(
        user="spammerMcSpammy",
        text="spammy message",
        user_id="123",
        event_id="messageid123",
    )

    remove_event = opsdroid_events.DeleteMessage(linked_event=message_event)

    connector.send_message = amock.CoroutineMock()

    await connector.remove_message(remove_event)

    assert connector.send_message.called
    assert "messageid123" in caplog.text


@pytest.mark.asyncio
async def test_send_message_event(opsdroid, caplog):
    caplog.set_level(logging.DEBUG)
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)
    message_event = opsdroid_events.Message(text="Hello world!")

    connector.send_message = amock.CoroutineMock()

    await connector._send_message(message_event)

    assert connector.send_message.called
    assert "Hello world!" in caplog.text


@pytest.mark.asyncio
async def test_update_stream_title(opsdroid, caplog):
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)

    caplog.set_level(logging.DEBUG)

    post_response = amock.Mock()
    post_response.status = 204
    post_response.json = amock.CoroutineMock()

    with amock.patch(
        "aiohttp.ClientSession.patch", new=amock.CoroutineMock()
    ) as mocked_session:

        mocked_session.return_value = asyncio.Future()
        mocked_session.return_value.set_result(post_response)

        status_event = twitch_event.UpdateTitle(status="Test title!")

        await connector.update_stream_title(status_event)

        assert "Test title!" in caplog.text


@pytest.mark.asyncio
async def test_update_stream_title_failure(opsdroid, caplog):
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)

    caplog.set_level(logging.DEBUG)

    post_response = amock.Mock()
    post_response.status = 500
    post_response.message = "Internal Server Error"

    with amock.patch(
        "aiohttp.ClientSession.patch", new=amock.CoroutineMock()
    ) as mocked_session:

        mocked_session.return_value = asyncio.Future()
        mocked_session.return_value.set_result(post_response)

        status_event = twitch_event.UpdateTitle(status="Test title!")

        await connector.update_stream_title(status_event)

        assert "Failed to update Twitch channel title" in caplog.text


@pytest.mark.asyncio
async def test_handle_challenge(opsdroid, caplog):
    caplog.set_level(logging.DEBUG)

    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)

    req = make_mocked_request("GET", "/connector/twitch?hub.challenge=testchallenge123")

    resp = await connector.handle_challenge(req)

    assert "Failed to get challenge" not in caplog.text
    assert "testchallenge123" in resp.text


@pytest.mark.asyncio
async def test_handle_challenge_error(opsdroid, caplog):
    caplog.set_level(logging.DEBUG)

    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)

    req = make_mocked_request("GET", "/connector/twitch")

    resp = await connector.handle_challenge(req)

    assert "Failed to get challenge" in caplog.text
    assert resp.status == 500


@pytest.mark.asyncio
async def test_invalid_post_request_webhook(opsdroid):
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)
    connector.validate_request = amock.CoroutineMock(return_value=False)

    mock_request = amock.CoroutineMock()
    mock_request.json = amock.CoroutineMock()
    mock_request.json.return_value = {"data": [{"test": "test"}]}

    resp = await connector.twitch_webhook_handler(mock_request)

    assert "Unauthorized" in resp.text
    assert resp.status == 401


@pytest.mark.asyncio
async def test_stream_ended_event(opsdroid):
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)
    connector.validate_request = amock.CoroutineMock(return_value=True)
    connector.disconnect_websockets = amock.CoroutineMock()

    mock_request = amock.CoroutineMock()
    mock_request.json = amock.CoroutineMock()
    mock_request.json.return_value = {"data": []}

    twitch_event.StreamEnded = amock.Mock()

    resp = await connector.twitch_webhook_handler(mock_request)

    assert not connector.is_live
    assert resp.status == 200
    assert twitch_event.StreamEnded.called


@pytest.mark.asyncio
async def test_followed_event(opsdroid, caplog):
    caplog.set_level(logging.DEBUG)
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)
    connector.validate_request = amock.CoroutineMock(return_value=True)

    mock_request = amock.CoroutineMock()
    mock_request.json = amock.CoroutineMock()
    mock_request.json.return_value = {
        "data": [{"from_name": "awesome_follower", "followed_at": "today"}]
    }
    follow_event = twitch_event.UserFollowed("awesome_follower", "today")
    twitch_event.UserFollowed = amock.Mock()

    resp = await connector.twitch_webhook_handler(mock_request)

    assert "Follower event received by Twitch." in caplog.text
    assert resp.status == 200
    assert twitch_event.UserFollowed.called
    assert "awesome_follower" in follow_event.follower
    assert "today" in follow_event.followed_at


def test_user_subscribed():
    event = twitch_event.UserSubscribed("user_mc_user", "Hello!")

    assert "user_mc_user" in event.user
    assert "Hello!" in event.message


@pytest.mark.asyncio
async def test_gift_subscription_event(opsdroid, caplog):
    caplog.set_level(logging.DEBUG)
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)
    connector.validate_request = amock.CoroutineMock(return_value=True)

    mock_request = amock.CoroutineMock()
    mock_request.json = amock.CoroutineMock()
    mock_request.json.return_value = {
        "data": [
            {
                "event_type": "subscriptions.subscribe",
                "event_data": {
                    "user_name": "lucky_mc_luck",
                    "gifter_name": "Awesome gifter",
                    "is_gift": True,
                },
            }
        ]
    }

    twitch_event.UserSubscribed = amock.Mock()

    resp = await connector.twitch_webhook_handler(mock_request)

    assert "Gifted subscriber event received by Twitch." in caplog.text
    assert resp.status == 200
    assert twitch_event.UserSubscribed.called


@pytest.mark.asyncio
async def test_subscription_event(opsdroid, caplog):
    caplog.set_level(logging.DEBUG)
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)
    connector.validate_request = amock.CoroutineMock(return_value=True)

    mock_request = amock.CoroutineMock()
    mock_request.json = amock.CoroutineMock()
    mock_request.json.return_value = {
        "data": [
            {
                "event_type": "subscriptions.notification",
                "event_data": {
                    "user_name": "awesome_subscriber!",
                    "message": "Best channel ever!",
                },
            }
        ]
    }

    twitch_event.UserSubscribed = amock.Mock()

    resp = await connector.twitch_webhook_handler(mock_request)

    assert "Subscriber event received by Twitch." in caplog.text
    assert resp.status == 200
    assert twitch_event.UserSubscribed.called


@pytest.mark.asyncio
async def test_stream_started_event(opsdroid, caplog):
    caplog.set_level(logging.DEBUG)
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)
    connector.validate_request = amock.CoroutineMock(return_value=True)
    connector.listen = amock.CoroutineMock()

    mock_request = amock.CoroutineMock()
    mock_request.json = amock.CoroutineMock()
    mock_request.json.return_value = {
        "data": [
            {
                "started_at": "just now",
                "title": "Testing with pytest!",
                "viewer_count": 1,
            }
        ]
    }

    stream_start_event = twitch_event.StreamStarted(
        "Testing with pytest", 1, "just now"
    )

    twitch_event.StreamStarted = amock.Mock()

    resp = await connector.twitch_webhook_handler(mock_request)

    assert "Broadcaster went live event received by Twitch." in caplog.text
    assert connector.is_live
    assert resp.status == 200
    assert twitch_event.StreamStarted.called
    assert connector.listen.called
    assert "Testing with pytest" in stream_start_event.title
    assert 1 == stream_start_event.viewers
    assert "just now" in stream_start_event.started_at


@pytest.mark.asyncio
async def test_disconnect(opsdroid):
    connector_config["always-listening"] = True
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)

    connector.disconnect_websockets = amock.CoroutineMock()
    connector.webhook = amock.CoroutineMock()

    await connector.disconnect()

    assert connector.is_live is True
    assert connector.disconnect_websockets.called
    assert connector.webhook.called


@pytest.mark.asyncio
async def test_get_message_loop(opsdroid):

    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)

    connector.websocket = amock.MagicMock()
    connector.websocket.__aiter__.return_value = [
        WSMessage(WSMsgType.TEXT, "PING", b""),
        WSMessage(WSMsgType.TEXT, ":user@user.twitch.tmi! JOIN #channel", b""),
        WSMessage(WSMsgType.CLOSED, "CLOSE", ""),
    ]

    connector.websocket.send_str = amock.CoroutineMock()
    connector.websocket.close = amock.CoroutineMock()
    connector._handle_message = amock.CoroutineMock()

    with pytest.raises(ConnectionError):
        await connector.get_messages_loop()

        assert connector.is_live
        assert connector.send_str.called
        assert connector.websocket.close.called
        assert connector._handle_message.called


@pytest.mark.asyncio
async def test_handle_message_chat_message(opsdroid, caplog):
    caplog.set_level(logging.DEBUG)
    message = "@badge-info=;badges=;client-nonce=jiwej12;color=;display-name=user;emotes=;flags=0-81:;id=jdias-9212;mod=0;room-id=123;subscriber=0;tmi-sent-ts=1592943868712;turbo=0;user-id=123;user-type= :user!user@user.tmi.twitch.tv PRIVMSG #channel :Hello world!"

    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)

    opsdroid.parse = amock.CoroutineMock()

    await connector._handle_message(message)

    assert "Got message from Twitch" in caplog.text
    assert opsdroid.parse.called


@pytest.mark.asyncio
async def test_handle_message_join_event(opsdroid):
    message = ":user!user@user.tmi.twitch.tv JOIN #channel"

    join_event = opsdroid_events.JoinRoom(user="username")

    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)

    opsdroid.parse = amock.CoroutineMock()

    await connector._handle_message(message)

    assert opsdroid.parse.called
    assert "username" in join_event.user


@pytest.mark.asyncio
async def test_handle_message_left_event(opsdroid):
    message = ":user!user@user.tmi.twitch.tv PART #channel"

    left_event = opsdroid_events.LeaveRoom(user="username")

    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)

    opsdroid.parse = amock.CoroutineMock()

    await connector._handle_message(message)
    assert opsdroid.parse.called
    assert "username" in left_event.user


@pytest.mark.asyncio
async def test_handle_message_authentication_failed(opsdroid):
    message = ":tmi.twitch.tv NOTICE * :Login authentication failed"

    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)

    connector.refresh_token = amock.CoroutineMock()

    with pytest.raises(ConnectionError):
        await connector._handle_message(message)

        assert connector.refresh_token.called


@pytest.mark.asyncio
async def test_disconnect_websockets(opsdroid):
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)

    connector.websocket = web.WebSocketResponse()

    resp = await connector.disconnect_websockets()

    assert not connector.websocket
    assert not connector.is_live
    assert not resp


@pytest.mark.asyncio
async def test_listen(opsdroid):
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)

    with amock.patch(
        "aiohttp.ClientSession.ws_connect", new=amock.CoroutineMock()
    ) as mocked_websocket:
        mocked_websocket.side_effect = Exception()

        with contextlib.suppress(Exception):
            await connector.listen()


@pytest.mark.asyncio
async def test_listen_reconnect(opsdroid, caplog):
    caplog.set_level(logging.DEBUG)
    connector = ConnectorTwitch(connector_config, opsdroid=opsdroid)
    connector.connect_websocket = amock.CoroutineMock(side_effect=ConnectionError)

    with amock.patch(
        "aiohttp.ClientSession.ws_connect", new=amock.CoroutineMock()
    ) as mocked_websocket, amock.patch("asyncio.sleep") as mocked_sleep:
        mocked_websocket.side_effect = Exception()

        with contextlib.suppress((Exception)):
            await connector.listen()

            assert mocked_sleep.called
            assert None in caplog.text
            assert connector.reconnections == 1
