"""Tests for the ConnectorMatrix class."""
import asyncio
from unittest import mock

import aiohttp
import asynctest
import asynctest.mock as amock
from matrix_api_async import AsyncHTTPAPI
from matrix_client.errors import MatrixRequestError

from opsdroid.core import OpsDroid
from opsdroid.events import Image, File, Message
from opsdroid.connector.matrix import ConnectorMatrix
from opsdroid.connector.matrix.create_events import MatrixEventCreator
from opsdroid.__main__ import configure_lang  # noqa

api_string = "matrix_api_async.AsyncHTTPAPI.{}"


def setup_connector():
    """Initiate a basic connector setup for testing on"""
    connector = ConnectorMatrix(
        {
            "room": "#test:localhost",
            "mxid": "@opsdroid:localhost",
            "password": "hello",
            "homeserver": "http://localhost:8008",
        }
    )
    return connector


class TestConnectorMatrixAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid Matrix connector class."""

    @property
    def sync_return(self):
        """Define some mock json to return from the sync method"""
        return {
            "account_data": {"events": []},
            "device_lists": {"changed": [], "left": []},
            "device_one_time_keys_count": {"signed_curve25519": 50},
            "groups": {"invite": {}, "join": {}, "leave": {}},
            "next_batch": "s801873745",
            "presence": {"events": []},
            "rooms": {
                "invite": {},
                "join": {
                    "!aroomid:localhost": {
                        "account_data": {"events": []},
                        "ephemeral": {"events": []},
                        "state": {"events": []},
                        "summary": {},
                        "timeline": {
                            "events": [
                                {
                                    "content": {
                                        "body": "LOUD NOISES",
                                        "msgtype": "m.text",
                                    },
                                    "event_id": "$eventid:localhost",
                                    "origin_server_ts": 1547124373956,
                                    "sender": "@cadair:cadair.com",
                                    "type": "m.room.message",
                                    "unsigned": {"age": 3498},
                                }
                            ],
                            "limited": False,
                            "prev_batch": "s801873709",
                        },
                        "unread_notifications": {
                            "highlight_count": 0,
                            "notification_count": 0,
                        },
                    }
                },
                "leave": {},
            },
            "to_device": {"events": []},
        }

    def setUp(self):
        """Basic setting up for tests"""
        self.connector = setup_connector()
        self.api = AsyncHTTPAPI("https://notaurl.com", None)
        self.connector.connection = self.api

    async def test_make_filter(self):
        with amock.patch(api_string.format("create_filter")) as patched_filter:
            patched_filter.return_value = asyncio.Future()
            patched_filter.return_value.set_result({"filter_id": "arbitrary string"})
            test_rooms = ["!notaroom:matrix.org", "!notanotherroom:matrix.org"]
            filter_id = await self.connector.make_filter(self.api, test_rooms)
            assert filter_id == "arbitrary string"

            assert patched_filter.called
            assert patched_filter.call_args[1]["user_id"] == "@opsdroid:localhost"
            assert (
                patched_filter.call_args[1]["filter_params"]["room"]["rooms"]
                == test_rooms
            )

    async def test_connect(self):
        with amock.patch(api_string.format("login")) as patched_login, amock.patch(
            api_string.format("join_room")
        ) as patched_join_room, amock.patch(
            api_string.format("create_filter")
        ) as patched_filter, amock.patch(
            api_string.format("sync")
        ) as patched_sync, amock.patch(
            api_string.format("get_display_name")
        ) as patched_get_nick, amock.patch(
            api_string.format("set_display_name")
        ) as patch_set_nick, amock.patch(
            "aiohttp.ClientSession"
        ) as patch_cs, OpsDroid() as opsdroid:

            # Skip actually creating a client session
            patch_cs.return_value = amock.MagicMock()

            patched_login.return_value = asyncio.Future()
            patched_login.return_value.set_result({"access_token": "arbitrary string1"})

            patched_join_room.return_value = asyncio.Future()
            patched_join_room.return_value.set_result({"room_id": "!aroomid:localhost"})

            patched_filter.return_value = asyncio.Future()
            patched_filter.return_value.set_result({"filter_id": "arbitrary string"})

            patched_sync.return_value = asyncio.Future()
            patched_sync.return_value.set_result({"next_batch": "arbitrary string2"})

            await self.connector.connect()

            assert "!aroomid:localhost" in self.connector.room_ids.values()

            assert self.connector.connection.token == "arbitrary string1"

            assert self.connector.filter_id == "arbitrary string"

            assert self.connector.connection.sync_token == "arbitrary string2"

            self.connector.nick = "Rabbit Hole"

            patched_get_nick.return_value = asyncio.Future()
            patched_get_nick.return_value.set_result("Rabbit Hole")

            await self.connector.connect()

            assert patched_get_nick.called
            assert not patch_set_nick.called

            patched_get_nick.return_value = asyncio.Future()
            patched_get_nick.return_value.set_result("Neo")

            self.connector.mxid = "@morpheus:matrix.org"

            await self.connector.connect()

            assert patched_get_nick.called
            patch_set_nick.assert_called_once_with(
                "@morpheus:matrix.org", "Rabbit Hole"
            )

    async def test_parse_sync_response(self):
        self.connector.room_ids = {"main": "!aroomid:localhost"}
        self.connector.filter_id = "arbitrary string"

        with amock.patch(api_string.format("get_display_name")) as patched_name:
            patched_name.return_value = asyncio.Future()
            patched_name.return_value.set_result("SomeUsersName")

            returned_message = await self.connector._parse_sync_response(
                self.sync_return
            )

            assert returned_message.text == "LOUD NOISES"
            assert returned_message.user == "SomeUsersName"
            assert returned_message.target == "!aroomid:localhost"
            assert returned_message.connector == self.connector
            raw_message = self.sync_return["rooms"]["join"]["!aroomid:localhost"][
                "timeline"
            ]["events"][0]
            assert returned_message.raw_event == raw_message

    async def test_get_nick(self):
        self.connector.room_specific_nicks = True

        with amock.patch(
            api_string.format("get_room_displayname")
        ) as patched_roomname, amock.patch(
            api_string.format("get_display_name")
        ) as patched_globname:
            patched_roomname.return_value = asyncio.Future()
            patched_roomname.return_value.set_result("")

            mxid = "@notaperson:matrix.org"
            assert await self.connector.get_nick("#notaroom:localhost", mxid) == ""
            # Test if a room displayname couldn't be found
            patched_roomname.side_effect = Exception()

            # Test if that leads to a global displayname being returned
            patched_globname.return_value = asyncio.Future()
            patched_globname.return_value.set_result("@notaperson")
            assert (
                await self.connector.get_nick("#notaroom:localhost", mxid)
                == "@notaperson"
            )

            # Test that failed nickname lookup returns the mxid
            patched_globname.side_effect = MatrixRequestError()
            assert await self.connector.get_nick("#notaroom:localhost", mxid) == mxid

    async def test_get_formatted_message_body(self):
        original_html = "<p><h3><no>Hello World</no></h3></p>"
        original_body = "### Hello World"
        message = self.connector._get_formatted_message_body(original_html)
        assert message["formatted_body"] == "<h3>Hello World</h3>"
        assert message["body"] == "Hello World"

        message = self.connector._get_formatted_message_body(
            original_html, original_body
        )
        assert message["formatted_body"] == "<h3>Hello World</h3>"
        assert message["body"] == "### Hello World"

    async def _get_message(self):
        self.connector.room_ids = {"main": "!aroomid:localhost"}
        self.connector.filter_id = "arbitrary string"
        m = "opsdroid.connector.matrix.ConnectorMatrix.get_nick"

        with amock.patch(m) as patched_nick:
            patched_nick.return_value = asyncio.Future()
            patched_nick.return_value.set_result("Neo")

            return await self.connector._parse_sync_response(self.sync_return)

    async def test_respond_retry(self):
        message = await self._get_message()
        with amock.patch(api_string.format("send_message_event")) as patched_send:
            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result(None)
            await self.connector.send(message)

            message_obj = self.connector._get_formatted_message_body(message.text)
            patched_send.assert_called_once_with(
                message.target, "m.room.message", message_obj
            )

            patched_send.side_effect = [
                aiohttp.client_exceptions.ServerDisconnectedError(),
                patched_send.return_value,
            ]

            await self.connector.send(message)

            message_obj = self.connector._get_formatted_message_body(message.text)
            patched_send.assert_called_with(
                message.target, "m.room.message", message_obj
            )

    async def test_respond_room(self):
        message = await self._get_message()
        with amock.patch(
            api_string.format("send_message_event")
        ) as patched_send, amock.patch(
            api_string.format("get_room_id")
        ) as patched_room_id:

            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result(None)

            patched_room_id.return_value = asyncio.Future()
            patched_room_id.return_value.set_result(message.target)

            message.target = "main"
            await self.connector.send(message)

            message_obj = self.connector._get_formatted_message_body(message.text)
            patched_send.assert_called_once_with(
                "!aroomid:localhost", "m.room.message", message_obj
            )

    async def test_disconnect(self):
        self.connector.session = amock.MagicMock()
        self.connector.session.close = amock.CoroutineMock()
        await self.connector.disconnect()
        assert self.connector.session.close.called

    def test_get_roomname(self):
        self.connector.rooms = ["#notthisroom:localhost", "#thisroom:localhost"]
        self.connector.room_ids = dict(
            zip(
                self.connector.rooms, ["!aroomid:localhost", "!anotherroomid:localhost"]
            )
        )

        assert (
            self.connector.get_roomname("#thisroom:localhost") == "#thisroom:localhost"
        )
        assert (
            self.connector.get_roomname("!anotherroomid:localhost")
            == "#thisroom:localhost"
        )
        assert self.connector.get_roomname("someroom") == "someroom"

    async def test_respond_image(self):
        gif_bytes = (
            b"GIF89a\x01\x00\x01\x00\x00\xff\x00,"
            b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;"
        )

        image = Image(file_bytes=gif_bytes)
        with amock.patch(
            api_string.format("send_content")
        ) as patched_send, amock.patch(
            api_string.format("media_upload")
        ) as patched_upload:

            patched_upload.return_value = asyncio.Future()
            patched_upload.return_value.set_result({"content_uri": "mxc://aurl"})

            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result(None)
            await self.connector.send(image)

            patched_send.assert_called_once_with(
                "#test:localhost",
                "mxc://aurl",
                "opsdroid_upload",
                "m.image",
                {"w": 1, "h": 1, "mimetype": "image/gif", "size": 26},
            )

    async def test_respond_mxc(self):
        gif_bytes = (
            b"GIF89a\x01\x00\x01\x00\x00\xff\x00,"
            b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;"
        )

        image = Image(url="mxc://aurl")
        with amock.patch(
            api_string.format("send_content")
        ) as patched_send, amock.patch(
            "opsdroid.events.Image.get_file_bytes"
        ) as patched_bytes:

            patched_bytes.return_value = asyncio.Future()
            patched_bytes.return_value.set_result(gif_bytes)

            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result(None)
            await self.connector.send(image)

            patched_send.assert_called_once_with(
                "#test:localhost",
                "mxc://aurl",
                "opsdroid_upload",
                "m.image",
                {"w": 1, "h": 1, "mimetype": "image/gif", "size": 26},
            )

    async def test_respond_file(self):
        file_event = File(file_bytes=b"aslkdjlaksdjlkajdlk")
        with amock.patch(
            api_string.format("send_content")
        ) as patched_send, amock.patch(
            api_string.format("media_upload")
        ) as patched_upload:

            patched_upload.return_value = asyncio.Future()
            patched_upload.return_value.set_result({"content_uri": "mxc://aurl"})

            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result(None)
            await self.connector.send(file_event)

            patched_send.assert_called_once_with(
                "#test:localhost", "mxc://aurl", "opsdroid_upload", "m.file", {}
            )


class TestEventCreatorAsync(asynctest.TestCase):
    @property
    def message_json(self):
        return {
            "content": {"body": "I just did it manually.", "msgtype": "m.text"},
            "event_id": "$15573463541827394vczPd:matrix.org",
            "origin_server_ts": 1557346354253,
            "room_id": "!MeRdFpEonLoCwhoHeT:matrix.org",
            "sender": "@neo:matrix.org",
            "type": "m.room.message",
            "unsigned": {"age": 48926251},
            "user_id": "@nso:matrix.org",
            "age": 48926251,
        }

    @property
    def file_json(self):
        return {
            "origin_server_ts": 1534013434328,
            "sender": "@neo:matrix.org",
            "event_id": "$1534013434516721kIgMV:matrix.org",
            "content": {
                "body": "stereo_reproject.py",
                "info": {"mimetype": "text/x-python", "size": 1239},
                "msgtype": "m.file",
                "url": "mxc://matrix.org/vtgAIrGtuYJQCXNKRGhVfSMX",
            },
            "room_id": "!MeRdFpEonLoCwhoHeT:matrix.org",
            "type": "m.room.message",
            "unsigned": {"age": 23394532373},
            "user_id": "@neo:matrix.org",
            "age": 23394532373,
        }

    @property
    def image_json(self):
        return {
            "content": {
                "body": "index.png",
                "info": {
                    "h": 1149,
                    "mimetype": "image/png",
                    "size": 1949708,
                    "thumbnail_info": {
                        "h": 600,
                        "mimetype": "image/png",
                        "size": 568798,
                        "w": 612,
                    },
                    "thumbnail_url": "mxc://matrix.org/HjHqeJDDxcnOEGydCQlJZQwC",
                    "w": 1172,
                },
                "msgtype": "m.image",
                "url": "mxc://matrix.org/iDHKYJSQZZrrhOxAkMBMOaeo",
            },
            "event_id": "$15548652221495790FYlHC:matrix.org",
            "origin_server_ts": 1554865222742,
            "room_id": "!MeRdFpEonLoCwhoHeT:matrix.org",
            "sender": "@neo:matrix.org",
            "type": "m.room.message",
            "unsigned": {"age": 2542608318},
            "user_id": "@neo:matrix.org",
            "age": 2542608318,
        }

    @property
    def event_creator(self):
        connector = amock.MagicMock()
        patched_get_nick = amock.MagicMock()
        patched_get_nick.return_value = asyncio.Future()
        patched_get_nick.return_value.set_result("Rabbit Hole")
        connector.get_nick = patched_get_nick

        patched_get_download_url = mock.Mock()
        patched_get_download_url.return_value = "mxc://aurl"
        connector.connection.get_download_url = patched_get_download_url

        return MatrixEventCreator(connector)

    async def test_create_message(self):
        event = await self.event_creator.create_event(self.message_json, "hello")
        assert isinstance(event, Message)
        assert event.text == "I just did it manually."
        assert event.user == "Rabbit Hole"
        assert event.target == "hello"
        assert event.event_id == "$15573463541827394vczPd:matrix.org"
        assert event.raw_event == self.message_json

    async def test_create_file(self):
        event = await self.event_creator.create_event(self.file_json, "hello")
        assert isinstance(event, File)
        assert event.url == "mxc://aurl"
        assert event.user == "Rabbit Hole"
        assert event.target == "hello"
        assert event.event_id == "$1534013434516721kIgMV:matrix.org"
        assert event.raw_event == self.file_json

    async def test_create_image(self):
        event = await self.event_creator.create_event(self.image_json, "hello")
        assert isinstance(event, Image)
        assert event.url == "mxc://aurl"
        assert event.user == "Rabbit Hole"
        assert event.target == "hello"
        assert event.event_id == "$15548652221495790FYlHC:matrix.org"
        assert event.raw_event == self.image_json

    async def test_unsupported_type(self):
        json = self.message_json
        json["type"] = "wibble"
        event = await self.event_creator.create_event(json, "hello")
        assert event is None

    async def test_unsupported_message_type(self):
        json = self.message_json
        json["content"]["msgtype"] = "wibble"
        event = await self.event_creator.create_event(json, "hello")
        assert event is None
