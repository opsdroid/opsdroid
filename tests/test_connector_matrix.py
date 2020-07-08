"""Tests for the ConnectorMatrix class."""
import asyncio
from copy import deepcopy

import aiohttp

# import asynctest
import asynctest.mock as amock

# from pytest_mock import mocker

import nio
import pytest

import opsdroid.connector.matrix.events as matrix_events
from opsdroid.core import OpsDroid
from opsdroid import events
from opsdroid.connector.matrix import ConnectorMatrix
from opsdroid.connector.matrix.create_events import MatrixEventCreator
from opsdroid.cli.start import configure_lang  # noqa

api_string = "nio.AsyncClient.{}"


def setup_connector():
    """Initiate a basic connector setup for testing on"""
    connector = ConnectorMatrix(
        {
            "rooms": {"main": "#test:localhost"},
            "mxid": "@opsdroid:localhost",
            "password": "hello",
            "homeserver": "http://localhost:8008",
        }
    )
    return connector


@pytest.mark.asyncio
class TestConnectorMatrixAsync:
    """Test the async methods of the opsdroid Matrix connector class."""

    #    @pytest.fixture(autouse=True)
    #    def inject_fixtures(self, caplog):
    #        caplog = caplog

    @property
    def sync_return(self):
        """Define some mock json to return from the sync method"""
        rooms = nio.Rooms(
            invite={},
            join={
                "!aroomid:localhost": nio.RoomInfo(
                    account_data={"events": []},
                    ephemeral={"events": []},
                    state={"events": []},
                    summary={},
                    timeline=nio.Timeline(
                        events=[
                            nio.RoomMessageText(
                                source={
                                    "content": {
                                        "body": "LOUD NOISES",
                                        "msgtype": "m.text",
                                    },
                                    "event_id": "$eventid:localhost",
                                    "origin_server_ts": 1547124373956,
                                    "sender": "@cadair:cadair.com",
                                    "type": "m.room.message",
                                    "unsigned": {"age": 3498},
                                },
                                body="LOUD NOISES",
                                formatted_body="",
                                format="",
                            )
                        ],
                        limited=False,
                        prev_batch="s801873709",
                    ),
                )
            },
            leave={},
        )
        return nio.SyncResponse(
            next_batch="s801873745",
            rooms=rooms,
            device_key_count={"signed_curve25519": 50},
            device_list={"changed": [], "left": []},
            to_device_events={"events": []},
            presence_events={"events": []},
        )

    @property
    def sync_return_join(self):
        """Define some mock json to return from the sync method"""
        rooms = nio.Rooms(
            invite={},
            join={
                "!aroomid:localhost": nio.RoomInfo(
                    account_data={"events": []},
                    ephemeral={"events": []},
                    state={"events": []},
                    summary={},
                    timeline=nio.Timeline(
                        events=[
                            nio.RoomMemberEvent(
                                source={
                                    "origin_server_ts": 1591876480893,
                                    "sender": "@user:matrix.org",
                                    "type": "m.room.member",
                                    "unsigned": {
                                        "prev_content": {"membership": "invite"},
                                        "prev_sender": "@user:matrix.org",
                                    },
                                    "event_id": "$eventid:localhost",
                                },
                                state_key="@user:matrix.org",
                                membership="join",
                                prev_membership="invite",
                                content={"membership": "join"},
                                prev_content={"membership": "invite"},
                            )
                        ],
                        limited=False,
                        prev_batch="s801873709",
                    ),
                )
            },
            leave={},
        )
        return nio.SyncResponse(
            next_batch="s801873745",
            rooms=rooms,
            device_key_count={"signed_curve25519": 50},
            device_list={"changed": [], "left": []},
            to_device_events={"events": []},
            presence_events={"events": []},
        )

    @property
    def sync_invite(self):
        rooms = nio.Rooms(
            invite={
                "!AWtmOvkBPTCSPbdaHn:localhost": nio.InviteInfo(
                    invite_state=[
                        nio.InviteNameEvent(
                            source={
                                "type": "m.room.name",
                                "state_key": "",
                                "content": {"name": "Someroomname"},
                                "sender": "@neo:matrix.org",
                            },
                            sender="@neo:matrix.org",
                            name="Someroomname",
                        ),
                        nio.InviteMemberEvent(
                            source={
                                "type": "m.room.member",
                                "state_key": "@neo:matrix.org",
                                "sender": "@neo:matrix.org",
                            },
                            sender="@neo:matrix.org",
                            state_key="@neo:matrix.org",
                            membership="join",
                            prev_membership=None,
                            content={
                                "membership": "join",
                                "displayname": "stuart",
                                "avatar_url": None,
                            },
                            prev_content=None,
                        ),
                        nio.InviteMemberEvent(
                            source={
                                "type": "m.room.member",
                                "sender": "@neo:matrix.org",
                                "state_key": "@opsdroid:opsdroid.dev",
                                "origin_server_ts": 1575509408883,
                                "unsigned": {"age": 150},
                                "event_id": "$tibhPrUV0GJbb3-7Iad_LuYzTnB2vcdf4wBbHNXkQMc",
                            },
                            sender="@neo:matrix.org",
                            state_key="@opsdroid:opsdroid.dev",
                            membership="invite",
                            prev_membership=None,
                            content={
                                "membership": "invite",
                                "displayname": "Opsdroid",
                                "avatar_url": None,
                            },
                            prev_content=None,
                        ),
                    ]
                )
            },
            join={},
            leave={},
        )
        return nio.SyncResponse(
            next_batch="s110_1482_2_21_3_1_1_39_1",
            rooms=rooms,
            device_key_count={},
            device_list={"changed": [], "left": []},
            to_device_events={"events": []},
            presence_events={"events": []},
        )

    @property
    def filter_json(self):
        return {
            "event_format": "client",
            "account_data": {"limit": 0, "types": []},
            "presence": {"limit": 0, "types": []},
            "room": {
                "account_data": {"types": []},
                "ephemeral": {"types": []},
                "state": {"types": []},
            },
        }

    #    def setUp(self):
    #        """Basic setting up for tests"""
    connector = setup_connector()
    api = nio.AsyncClient("https://notaurl.com", None)
    connector.connection = api

    async def test_make_filter(self):
        with amock.patch(api_string.format("send")) as patched_filter:

            connect_response = amock.Mock()
            connect_response.status = 200
            connect_response.json = amock.CoroutineMock()
            connect_response.json.return_value = {"filter_id": 10}

            self.api.token = "abc"

            patched_filter.return_value = asyncio.Future()
            patched_filter.return_value.set_result(connect_response)

            filter_id = await self.connector.make_filter(self.api, self.filter_json)

            assert filter_id == 10
            assert patched_filter.called

    async def test_connect(self, caplog):
        with amock.patch(api_string.format("login")) as patched_login, amock.patch(
            api_string.format("join")
        ) as patched_join, amock.patch(
            api_string.format("sync")
        ) as patched_sync, amock.patch(
            api_string.format("send")
        ) as patched_filter, amock.patch(
            api_string.format("get_displayname")
        ) as patched_get_nick, amock.patch(
            api_string.format("set_displayname")
        ) as patch_set_nick, amock.patch(
            api_string.format("send_to_device_messages")
        ) as patched_send_to_device, amock.patch(
            api_string.format("should_upload_keys")
        ) as patched_should_upload, amock.patch(
            api_string.format("should_query_keys")
        ) as patched_should_query, amock.patch(
            api_string.format("keys_upload")
        ) as patched_keys_upload, amock.patch(
            api_string.format("keys_query")
        ) as patched_keys_query, amock.patch(
            "pathlib.Path.mkdir"
        ) as patched_mkdir, amock.patch(
            "pathlib.Path.is_dir"
        ) as patched_is_dir, amock.patch(
            "aiohttp.ClientSession"
        ) as patch_cs, OpsDroid() as _:

            # Skip actually creating a client session
            patch_cs.return_value = amock.MagicMock()

            patched_login.return_value = asyncio.Future()
            patched_login.return_value.set_result(
                nio.LoginResponse(
                    user_id="@opsdroid:localhost",
                    device_id="testdevice",
                    access_token="arbitrary string1",
                )
            )

            patched_join.return_value = asyncio.Future()
            patched_join.return_value.set_result(
                nio.JoinResponse(room_id="!aroomid:localhost")
            )

            patched_sync.return_value = asyncio.Future()
            patched_sync.return_value.set_result(
                nio.SyncResponse(
                    next_batch="arbitrary string2",
                    rooms={},
                    device_key_count={"signed_curve25519": 50},
                    device_list={"changed": [], "left": []},
                    to_device_events={"events": []},
                    presence_events={"events": []},
                )
            )

            connect_response = amock.Mock()
            connect_response.status = 200
            connect_response.json = amock.CoroutineMock()
            connect_response.return_value = {"filter_id": 1}

            patched_filter.return_value = asyncio.Future()
            patched_filter.return_value.set_result(connect_response)

            patch_set_nick.return_value = asyncio.Future()
            patch_set_nick.return_value.set_result(nio.ProfileSetDisplayNameResponse())

            patched_is_dir.return_value = False
            patched_mkdir.return_value = None

            patched_send_to_device.return_value = asyncio.Future()
            patched_send_to_device.return_value.set_result(None)

            patched_should_upload.return_value = True
            patched_keys_upload.return_value = asyncio.Future()
            patched_keys_upload.return_value.set_result(None)

            patched_should_query.return_value = True
            patched_keys_query.return_value = asyncio.Future()
            patched_keys_query.return_value.set_result(None)

            await self.connector.connect()

            if nio.crypto.ENCRYPTION_ENABLED:
                assert patched_mkdir.called

                assert patched_send_to_device.called
                assert patched_keys_upload.called
                assert patched_keys_query.called

            assert "!aroomid:localhost" in self.connector.room_ids.values()

            assert self.connector.connection.token == "arbitrary string1"

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
            patch_set_nick.assert_called_once_with("Rabbit Hole")

            error_message = "Some error message"
            error_code = 400

            # test sync error
            patched_sync.return_value = asyncio.Future()
            patched_sync.return_value.set_result(
                nio.SyncError(message=error_message, status_code=error_code)
            )
            caplog.clear()
            await self.connector.connect()
            assert [
                f"Error during initial sync: {error_message} (status code {error_code})"
            ] == [rec.message for rec in caplog.records]

            # test join error
            patched_sync.return_value = asyncio.Future()
            patched_sync.return_value.set_result(
                nio.SyncResponse(
                    next_batch="arbitrary string2",
                    rooms={},
                    device_key_count={"signed_curve25519": 50},
                    device_list={"changed": [], "left": []},
                    to_device_events={"events": []},
                    presence_events={"events": []},
                )
            )
            patched_join.return_value = asyncio.Future()
            patched_join.return_value.set_result(
                nio.JoinError(message=error_message, status_code=error_code)
            )
            caplog.clear()
            await self.connector.connect()
            assert [
                f"Error while joining room: {self.connector.rooms['main']['alias']}, Message: {error_message} (status code {error_code})"
            ] == [rec.message for rec in caplog.records]

            # test login error
            patched_login.return_value = asyncio.Future()
            patched_login.return_value.set_result(
                nio.LoginError(message=error_message, status_code=error_code)
            )
            caplog.clear()
            await self.connector.connect()
            assert [
                f"Error while connecting: {error_message} (status code {error_code})"
            ] == [rec.message for rec in caplog.records]

    async def test_parse_sync_response(self):
        self.connector.room_ids = {"main": "!aroomid:localhost"}
        self.connector.filter_id = "arbitrary string"

        with amock.patch(api_string.format("get_displayname")) as patched_name:

            patched_name.return_value = asyncio.Future()
            patched_name.return_value.set_result(
                nio.ProfileGetDisplayNameResponse("SomeUsersName")
            )

            returned_message = await self.connector._parse_sync_response(
                self.sync_return
            )

            assert isinstance(returned_message, events.Message)
            assert returned_message.text == "LOUD NOISES"
            assert returned_message.user == "SomeUsersName"
            assert returned_message.target == "!aroomid:localhost"
            assert returned_message.connector == self.connector
            raw_message = (
                self.sync_return.rooms.join["!aroomid:localhost"]
                .timeline.events[0]
                .source
            )
            assert returned_message.raw_event == raw_message

            returned_message = await self.connector._parse_sync_response(
                self.sync_return_join
            )

            assert isinstance(returned_message, events.JoinRoom)
            assert returned_message.user == "SomeUsersName"
            assert returned_message.target == "!aroomid:localhost"
            assert returned_message.connector == self.connector
            raw_message = (
                self.sync_return_join.rooms.join["!aroomid:localhost"]
                .timeline.events[0]
                .source
            )
            raw_message["content"] = {"membership": "join"}
            assert returned_message.raw_event == raw_message

    async def test_sync_parse_invites(self):
        with amock.patch(api_string.format("get_displayname")) as patched_name:
            self.connector.opsdroid = amock.MagicMock()
            self.connector.opsdroid.parse.return_value = asyncio.Future()
            self.connector.opsdroid.parse.return_value.set_result("")
            patched_name.return_value = asyncio.Future()
            patched_name.return_value.set_result(
                nio.ProfileGetDisplayNameResponse("SomeUsersName")
            )

            await self.connector._parse_sync_response(self.sync_invite)

            (invite,), _ = self.connector.opsdroid.parse.call_args

            assert invite.target == "!AWtmOvkBPTCSPbdaHn:localhost"
            assert invite.user == "SomeUsersName"
            assert invite.user_id == "@neo:matrix.org"
            assert invite.connector is self.connector

    async def test_get_nick(self):
        self.connector.room_specific_nicks = False

        with amock.patch(api_string.format("get_displayname")) as patched_globname:

            mxid = "@notaperson:matrix.org"

            patched_globname.return_value = asyncio.Future()
            patched_globname.return_value.set_result(
                nio.ProfileGetDisplayNameResponse(displayname="notaperson")
            )
            assert (
                await self.connector.get_nick("#notaroom:localhost", mxid)
                == "notaperson"
            )

    async def test_get_room_specific_nick(self, caplog):
        self.connector.room_specific_nicks = True

        with amock.patch(
            api_string.format("get_displayname")
        ) as patched_globname, amock.patch(
            api_string.format("joined_members")
        ) as patched_joined:

            mxid = "@notaperson:matrix.org"

            patched_globname.return_value = asyncio.Future()
            patched_globname.return_value.set_result(
                nio.ProfileGetDisplayNameResponse(displayname="notaperson")
            )

            patched_joined.return_value = asyncio.Future()
            patched_joined.return_value.set_result(
                nio.JoinedMembersResponse(
                    members=[
                        nio.RoomMember(
                            user_id="@notaperson:matrix.org",
                            display_name="notaperson",
                            avatar_url="",
                        )
                    ],
                    room_id="notanid",
                )
            )

            assert (
                await self.connector.get_nick("#notaroom:localhost", mxid)
                == "notaperson"
            )

            assert await self.connector.get_nick(None, mxid) == "notaperson"

            # test member not in list
            patched_joined.return_value = asyncio.Future()
            patched_joined.return_value.set_result(
                nio.JoinedMembersResponse(members=[], room_id="notanid")
            )
            assert await self.connector.get_nick("#notaroom:localhost", mxid) == mxid

            # test JoinedMembersError
            patched_joined.return_value = asyncio.Future()
            patched_joined.return_value.set_result(
                nio.JoinedMembersError(message="Some error", status_code=400)
            )
            caplog.clear()
            assert (
                await self.connector.get_nick("#notaroom:localhost", mxid)
                == "notaperson"
            )
            assert ["Failed to lookup room members for #notaroom:localhost."] == [
                rec.message for rec in caplog.records
            ]

            # test displayname is not set
            patched_globname.return_value = asyncio.Future()
            patched_globname.return_value.set_result(
                nio.ProfileGetDisplayNameResponse(displayname=None)
            )
            caplog.clear()
            assert await self.connector.get_nick("#notaroom:localhost", mxid) == mxid
            assert ["Failed to lookup room members for #notaroom:localhost."] == [
                rec.message for rec in caplog.records
            ]

            # test ProfileGetDisplayNameError
            patched_globname.return_value = asyncio.Future()
            patched_globname.return_value.set_result(
                nio.ProfileGetDisplayNameError(message="Some error", status_code=400)
            )
            caplog.clear()
            assert await self.connector.get_nick("#notaroom:localhost", mxid) == mxid
            assert f"Failed to lookup nick for {mxid}." == caplog.records[1].message

    async def test_get_nick_not_set(self):
        self.connector.room_specific_nicks = False

        with amock.patch(api_string.format("get_displayname")) as patched_globname:

            mxid = "@notaperson:matrix.org"

            # Test that failed nickname lookup returns the mxid
            patched_globname.return_value = asyncio.Future()
            patched_globname.return_value.set_result(
                nio.ProfileGetDisplayNameResponse(displayname=None)
            )
            assert await self.connector.get_nick("#notaroom:localhost", mxid) == mxid

    async def test_get_nick_error(self):
        self.connector.room_specific_nicks = False

        with amock.patch(api_string.format("get_displayname")) as patched_globname:

            mxid = "@notaperson:matrix.org"

            # Test if that leads to a global displayname being returned
            patched_globname.return_value = asyncio.Future()
            patched_globname.return_value.set_result(
                nio.ProfileGetDisplayNameError(message="Error")
            )
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

    async def test_send_edited_message(self):
        message = events.EditedMessage(
            text="New message",
            target="!test:localhost",
            linked_event=events.Message("hello", event_id="$hello"),
            connector=self.connector,
        )
        with amock.patch(
            api_string.format("room_send")
        ) as patched_send, OpsDroid() as _:
            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result({})

            new_content = self.connector._get_formatted_message_body(message.text)
            content = {
                "msgtype": "m.text",
                "m.new_content": new_content,
                "body": f"* {new_content['body']}",
                "m.relates_to": {
                    "rel_type": "m.replace",
                    "event_id": message.linked_event.event_id,
                },
            }

            await self.connector.send(message)

            patched_send.assert_called_once_with(
                message.target,
                "m.room.message",
                content,
                ignore_unverified_devices=True,
            )

            # Test linked event as event id
            message.linked_event = "$hello"

            await self.connector.send(message)

            patched_send.assert_called_with(
                message.target,
                "m.room.message",
                content,
                ignore_unverified_devices=True,
            )

            # Test responding to an edit
            await message.respond(events.EditedMessage("hello"))

            patched_send.assert_called_with(
                message.target,
                "m.room.message",
                content,
                ignore_unverified_devices=True,
            )

    async def test_respond_retry(self):
        message = await self._get_message()
        with amock.patch(api_string.format("room_send")) as patched_send:
            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result(None)
            await self.connector.send(message)

            message_obj = self.connector._get_formatted_message_body(message.text)
            patched_send.assert_called_once_with(
                message.target,
                "m.room.message",
                message_obj,
                ignore_unverified_devices=True,
            )

            patched_send.side_effect = [
                aiohttp.client_exceptions.ServerDisconnectedError(),
                patched_send.return_value,
            ]

            await self.connector.send(message)

            message_obj = self.connector._get_formatted_message_body(message.text)
            patched_send.assert_called_with(
                message.target,
                "m.room.message",
                message_obj,
                ignore_unverified_devices=True,
            )

    async def test_respond_room(self):
        message = await self._get_message()
        with amock.patch(api_string.format("room_send")) as patched_send:

            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result(None)

            message.target = "main"
            await self.connector.send(message)

            message_obj = self.connector._get_formatted_message_body(message.text)
            patched_send.assert_called_once_with(
                "!aroomid:localhost",
                "m.room.message",
                message_obj,
                ignore_unverified_devices=True,
            )

    async def test_disconnect(self, mocker):
        mocker.patch(api_string.format("close"), return_value=asyncio.Future())

        await self.connector.disconnect()
        assert self.connector.connection.close.called

    def test_get_roomname(self):
        self.connector.rooms = {
            "main": {"alias": "#notthisroom:localhost"},
            "test": {"alias": "#thisroom:localhost"},
        }
        self.connector.room_ids = dict(
            zip(
                self.connector.rooms.keys(),
                ["!aroomid:localhost", "!anotherroomid:localhost"],
            )
        )

        assert self.connector.get_roomname("#thisroom:localhost") == "test"
        assert self.connector.get_roomname("!aroomid:localhost") == "main"
        assert self.connector.get_roomname("someroom") == "someroom"

    def test_lookup_target(self):
        self.connector.room_ids = {
            "main": "!aroomid:localhost",
            "test": "#test:localhost",
        }

        assert self.connector.lookup_target("main") == "!aroomid:localhost"
        assert self.connector.lookup_target("#test:localhost") == "#test:localhost"
        assert (
            self.connector.lookup_target("!aroomid:localhost") == "!aroomid:localhost"
        )

    async def test_respond_image(self, mocker, caplog):
        gif_bytes = (
            b"GIF89a\x01\x00\x01\x00\x00\xff\x00,"
            b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;"
        )

        image = events.Image(file_bytes=gif_bytes, target="!test:localhost")

        patched_send = mocker.patch(
            api_string.format("room_send"), return_value=asyncio.Future()
        )
        patched_send.return_value.set_result(None)

        self.connector.connection.store = mocker.MagicMock()
        self.connector.connection.store.load_encrypted_rooms.return_value = []

        patched_upload = mocker.patch(
            api_string.format("upload"), return_value=asyncio.Future()
        )
        patched_upload.return_value.set_result([nio.UploadResponse("mxc://aurl"), None])

        await self.connector.send(image)

        patched_send.assert_called_once_with(
            room_id="!test:localhost",
            message_type="m.room.message",
            content={
                "body": "opsdroid_upload",
                "info": {"w": 1, "h": 1, "mimetype": "image/gif", "size": 26},
                "msgtype": "m.image",
                "url": "mxc://aurl",
            },
            ignore_unverified_devices=True,
        )

        file_dict = {
            "v": "v2",
            "key": {
                "kty": "oct",
                "alg": "A256CTR",
                "ext": True,
                "key_ops": ["encrypt", "decrypt"],
                "k": "randomkey",
            },
            "iv": "randomiv",
            "hashes": {"sha256": "shakey"},
            "url": "mxc://aurl",
            "mimetype": "image/gif",
        }

        self.connector.connection.store.load_encrypted_rooms.return_value = [
            "!test:localhost"
        ]
        patched_upload.return_value = asyncio.Future()
        patched_upload.return_value.set_result(
            [nio.UploadResponse("mxc://aurl"), file_dict]
        )

        await self.connector.send(image)

        patched_send.assert_called_with(
            room_id="!test:localhost",
            message_type="m.room.message",
            content={
                "body": "opsdroid_upload",
                "info": {"w": 1, "h": 1, "mimetype": "image/gif", "size": 26},
                "msgtype": "m.image",
                "file": file_dict,
            },
            ignore_unverified_devices=True,
        )

        error_message = "Some error message"
        error_code = 400
        self.connector.connection.store.load_encrypted_rooms.return_value = []
        patched_upload.return_value = asyncio.Future()
        patched_upload.return_value.set_result(
            [nio.UploadError(message=error_message, status_code=error_code), None]
        )

        caplog.clear()
        await self.connector.send(image)
        assert [
            f"Error while sending the file. Reason: {error_message} (status code {error_code})"
        ] == [rec.message for rec in caplog.records]

    async def test_respond_mxc(self):
        gif_bytes = (
            b"GIF89a\x01\x00\x01\x00\x00\xff\x00,"
            b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;"
        )

        image = events.Image(url="mxc://aurl", target="!test:localhost")
        with amock.patch(api_string.format("room_send")) as patched_send, amock.patch(
            "opsdroid.events.Image.get_file_bytes"
        ) as patched_bytes:

            patched_bytes.return_value = asyncio.Future()
            patched_bytes.return_value.set_result(gif_bytes)

            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result(None)
            await self.connector.send(image)

            patched_send.assert_called_once_with(
                content={
                    "body": "opsdroid_upload",
                    "info": {},
                    "msgtype": "m.image",
                    "url": "mxc://aurl",
                },
                message_type="m.room.message",
                room_id="!test:localhost",
                ignore_unverified_devices=True,
            )

    async def test_respond_file(self, mocker):
        file_event = events.File(
            file_bytes=b"aslkdjlaksdjlkajdlk",
            target="!test:localhost",
            mimetype="text/plain",
        )

        patched_send = mocker.patch(
            api_string.format("room_send"), return_value=asyncio.Future()
        )
        patched_send.return_value.set_result(None)

        self.connector.connection.store = mocker.MagicMock()
        self.connector.connection.store.load_encrypted_rooms.return_value = []

        patched_upload = mocker.patch(
            api_string.format("upload"), return_value=asyncio.Future()
        )
        patched_upload.return_value.set_result([nio.UploadResponse("mxc://aurl"), None])

        await self.connector.send(file_event)

        patched_send.assert_called_once_with(
            room_id="!test:localhost",
            message_type="m.room.message",
            content={
                "body": "opsdroid_upload",
                "info": {"mimetype": "text/plain", "size": 19},
                "msgtype": "m.file",
                "url": "mxc://aurl",
            },
            ignore_unverified_devices=True,
        )

        file_dict = {
            "v": "v2",
            "key": {
                "kty": "oct",
                "alg": "A256CTR",
                "ext": True,
                "key_ops": ["encrypt", "decrypt"],
                "k": "randomkey",
            },
            "iv": "randomiv",
            "hashes": {"sha256": "shakey"},
            "url": "mxc://aurl",
            "mimetype": "text/plain",
        }

        self.connector.connection.store.load_encrypted_rooms.return_value = [
            "!test:localhost"
        ]
        patched_upload.return_value = asyncio.Future()
        patched_upload.return_value.set_result(
            [nio.UploadResponse("mxc://aurl"), file_dict]
        )

        await self.connector.send(file_event)

        patched_send.assert_called_with(
            room_id="!test:localhost",
            message_type="m.room.message",
            content={
                "body": "opsdroid_upload",
                "info": {"mimetype": "text/plain", "size": 19},
                "msgtype": "m.file",
                "file": file_dict,
            },
            ignore_unverified_devices=True,
        )

    async def test_respond_new_room(self, caplog):
        event = events.NewRoom(name="test", target="!test:localhost")
        with amock.patch(api_string.format("room_create")) as patched_send, amock.patch(
            api_string.format("room_put_state")
        ) as patched_name:

            patched_name.return_value = asyncio.Future()
            patched_name.return_value.set_result(
                nio.RoomPutStateResponse(
                    room_id="!test:localhost",
                    event_id="$tibhPrUV0GJbb3-7Iad_LuYzTnB2vcdf4wBbHNXkQMc",
                )
            )

            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result(
                nio.RoomCreateResponse(room_id="!test:localhost")
            )

            resp = await self.connector.send(event)
            assert resp == "!test:localhost"

            assert patched_send.called_once_with(name="test")

            # test error
            error_message = "Some error message"
            error_code = 400
            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result(
                nio.RoomCreateError(message=error_message, status_code=error_code)
            )
            caplog.clear()
            resp = await self.connector.send(event)
            assert [
                f"Error while creating the room. Reason: {error_message} (status code {error_code})"
            ] == [rec.message for rec in caplog.records]

    async def test_respond_room_address(self):
        event = events.RoomAddress("#test:localhost", target="!test:localhost")

        with amock.patch(api_string.format("room_put_state")) as patched_send:
            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result({})

            await self.connector.send(event)

            assert patched_send.called_once_with("!test:localhost", "#test:localhost")

    async def test_respond_join_room(self):
        event = events.JoinRoom(target="#test:localhost")
        with amock.patch(
            api_string.format("room_resolve_alias")
        ) as patched_get_room_id, amock.patch(
            api_string.format("join")
        ) as patched_send:

            patched_get_room_id.return_value = asyncio.Future()
            patched_get_room_id.return_value.set_result(
                nio.RoomResolveAliasResponse(
                    room_alias="aroom", room_id="!aroomid:localhost", servers=[]
                )
            )

            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result({})
            await self.connector.send(event)
            assert patched_send.called_once_with("#test:localhost")

    async def test_respond_join_room_error(self, caplog):
        event = events.JoinRoom(target="#test:localhost")
        with amock.patch(
            api_string.format("room_resolve_alias")
        ) as patched_get_room_id, amock.patch(
            api_string.format("join")
        ) as patched_send:

            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result({})

            # test error
            error_message = "Some error message"
            error_code = 400
            patched_get_room_id.return_value = asyncio.Future()
            patched_get_room_id.return_value.set_result(
                nio.RoomResolveAliasError(message=error_message, status_code=error_code)
            )
            caplog.clear()
            await self.connector.send(event)
            assert patched_send.called_once_with("#test:localhost")
            assert patched_get_room_id.called_once_with("#test:localhost")
            assert [
                f"Error resolving room id for #test:localhost: {error_message} (status code {error_code})"
            ] == [rec.message for rec in caplog.records]

    async def test_respond_user_invite(self):
        event = events.UserInvite("@test:localhost", target="!test:localhost")
        with amock.patch(api_string.format("room_invite")) as patched_send:
            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result({})
            await self.connector.send(event)
            assert patched_send.called_once_with("#test:localhost", "@test:localhost")

    async def test_respond_room_description(self):
        event = events.RoomDescription("A test room", target="!test:localhost")

        with amock.patch(api_string.format("room_put_state")) as patched_send:
            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result({})
            await self.connector.send(event)
            assert patched_send.called_once_with("#test:localhost", "A test room")

    async def test_respond_room_image(self):
        image = events.Image(url="mxc://aurl")
        event = events.RoomImage(image, target="!test:localhost")

        with OpsDroid() as opsdroid, amock.patch(
            api_string.format("room_put_state")
        ) as patched_send:
            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result({})
            opsdroid.connectors = [self.connector]
            await self.connector.send(event)
            assert patched_send.called_once_with(
                "#test:localhost",
                "m.room.avatar",
                {"url": "mxc://aurl"},
                state_key=None,
                ignore_unverified_devices=True,
            )

    async def test_respond_user_role(self):
        existing_power_levels = {
            "ban": 50,
            "events": {"m.room.name": 100, "m.room.power_levels": 100},
            "events_default": 0,
            "invite": 50,
            "kick": 50,
            "notifications": {"room": 20},
            "redact": 50,
            "state_default": 50,
            "users": {"@example:localhost": 100},
            "users_default": 0,
        }
        role_events = [
            (
                events.UserRole(
                    75, target="!test:localhost", user_id="@test:localhost"
                ),
                75,
            ),
            (
                events.UserRole(
                    "mod", target="!test:localhost", user_id="@test:localhost"
                ),
                50,
            ),
            (
                events.UserRole(
                    "admin", target="!test:localhost", user_id="@test:localhost"
                ),
                100,
            ),
        ]
        for event, pl in role_events:

            with OpsDroid() as opsdroid, amock.patch(
                api_string.format("room_put_state")
            ) as patched_send:
                with amock.patch(
                    api_string.format("room_get_state_event")
                ) as patched_power_levels:
                    opsdroid.connectors = [self.connector]

                    patched_power_levels.return_value = asyncio.Future()
                    patched_power_levels.return_value.set_result(
                        nio.RoomGetStateEventResponse(
                            room_id="!test:localhost",
                            state_key="",
                            event_type="m.room.power_levels",
                            content=existing_power_levels,
                        )
                    )
                    patched_send.return_value = asyncio.Future()
                    patched_send.return_value.set_result({})

                    await self.connector.send(event)

                    modified_power_levels = deepcopy(existing_power_levels)
                    modified_power_levels["users"]["@test:localhost"] = pl

                    assert patched_send.called_once_with(
                        "!test:localhost",
                        "m.room.power_levels",
                        existing_power_levels,
                        state_key=None,
                    )

    async def test_send_reaction(self):
        message = events.Message(
            "hello",
            event_id="$11111",
            connector=self.connector,
            target="!test:localhost",
        )
        reaction = events.Reaction("⭕")
        with OpsDroid() as _:
            with amock.patch(api_string.format("room_send")) as patched_send:
                patched_send.return_value = asyncio.Future()
                patched_send.return_value.set_result(None)

                await message.respond(reaction)

                content = {
                    "m.relates_to": {
                        "rel_type": "m.annotation",
                        "event_id": "$11111",
                        "key": reaction.emoji,
                    }
                }

                assert patched_send.called_once_with(
                    "!test:localhost", "m.reaction", content
                )

    async def test_send_reply(self):
        message = events.Message(
            "hello",
            event_id="$11111",
            connector=self.connector,
            target="!test:localhost",
        )
        reply = events.Reply("reply")
        with OpsDroid() as _:
            with amock.patch(api_string.format("room_send")) as patched_send:
                patched_send.return_value = asyncio.Future()
                patched_send.return_value.set_result(None)

                await message.respond(reply)

                content = self.connector._get_formatted_message_body(
                    reply.text, msgtype="m.text"
                )

                content["m.relates_to"] = {
                    "m.in_reply_to": {"event_id": message.event_id}
                }

                assert patched_send.called_once_with(
                    "!test:localhost", "m.room.message", content
                )

    async def test_send_reply_id(self):
        reply = events.Reply("reply", linked_event="$hello", target="!hello:localhost")
        with OpsDroid() as _:
            with amock.patch(api_string.format("room_send")) as patched_send:
                patched_send.return_value = asyncio.Future()
                patched_send.return_value.set_result(None)

                await self.connector.send(reply)

                content = self.connector._get_formatted_message_body(
                    reply.text, msgtype="m.text"
                )

                content["m.relates_to"] = {"m.in_reply_to": {"event_id": "$hello"}}

                assert patched_send.called_once_with(
                    "!test:localhost", "m.room.message", content
                )

    async def test_alias_already_exists(self, caplog):

        with amock.patch(api_string.format("room_put_state")) as patched_alias:
            patched_alias.return_value = asyncio.Future()
            patched_alias.return_value.set_result(
                nio.RoomPutStateResponse(event_id="some_id", room_id="!test:localhost")
            )

            resp = await self.connector._send_room_address(
                events.RoomAddress(target="!test:localhost", address="hello")
            )
            assert resp.event_id == "some_id"
            assert resp.room_id == "!test:localhost"

            # test error
            error_message = "some error message"
            error_code = 400
            patched_alias.return_value = asyncio.Future()
            patched_alias.return_value.set_result(
                nio.RoomPutStateError(message=error_message, status_code=error_code)
            )
            caplog.clear()
            resp = await self.connector._send_room_address(
                events.RoomAddress(target="!test:localhost", address="hello")
            )
            assert [
                f"Error while setting room alias: {error_message} (status code {error_code})"
            ] == [rec.message for rec in caplog.records]

            error_code = 409
            patched_alias.return_value = asyncio.Future()
            patched_alias.return_value.set_result(
                nio.RoomPutStateError(message=error_message, status_code=error_code)
            )
            caplog.clear()
            resp = await self.connector._send_room_address(
                events.RoomAddress(target="!test:localhost", address="hello")
            )
            assert ["A room with the alias hello already exists."] == [
                rec.message for rec in caplog.records
            ]

    async def test_already_in_room(self, caplog):
        with amock.patch(api_string.format("room_invite")) as patched_invite:

            patched_invite.return_value = asyncio.Future()
            patched_invite.return_value.set_result(
                nio.RoomInviteError(
                    message="@neo.matrix.org is already in the room", status_code=400
                )
            )

            caplog.clear()
            resp = await self.connector._send_user_invitation(
                events.UserInvite(target="!test:localhost", user_id="@neo:matrix.org")
            )
            assert resp.message == "@neo.matrix.org is already in the room"
            assert [
                "Error while inviting user @neo:matrix.org to room !test:localhost: @neo.matrix.org is already in the room (status code 400)"
            ] == [rec.message for rec in caplog.records]

            patched_invite.return_value = asyncio.Future()
            patched_invite.return_value.set_result(
                nio.RoomInviteError(
                    message="@neo.matrix.org is already in the room", status_code=403
                )
            )
            resp = await self.connector._send_user_invitation(
                events.UserInvite(target="!test:localhost", user_id="@neo:matrix.org")
            )
            assert resp.message == "@neo.matrix.org is already in the room"

    async def test_invalid_role(self):
        with pytest.raises(ValueError):
            await self.connector._set_user_role(
                events.UserRole(
                    "wibble", target="!test:localhost", user_id="@test:localhost"
                )
            )

    async def test_no_user_id(self):
        with pytest.raises(ValueError):
            await self.connector._set_user_role(
                events.UserRole("wibble", target="!test:localhost")
            )

    def test_m_notice(self):
        self.connector.rooms["test"] = {
            "alias": "#test:localhost",
            "send_m_notice": True,
        }

        assert self.connector.message_type("main") == "m.text"
        assert self.connector.message_type("test") == "m.notice"
        self.connector.send_m_notice = True
        assert self.connector.message_type("main") == "m.notice"

        # Reset the state
        self.connector.send_m_notice = False
        del self.connector.rooms["test"]

    def test_construct(self):
        jr = matrix_events.MatrixJoinRules("hello")
        assert jr.content["join_rule"] == "hello"

        hv = matrix_events.MatrixHistoryVisibility("hello")
        assert hv.content["history_visibility"] == "hello"

    async def test_send_generic_event(self):
        event = matrix_events.GenericMatrixRoomEvent(
            "opsdroid.dev", {"hello": "world"}, target="!test:localhost"
        )
        with OpsDroid() as _:
            with amock.patch(api_string.format("room_send")) as patched_send:
                patched_send.return_value = asyncio.Future()
                patched_send.return_value.set_result(None)

                await self.connector.send(event)
                assert patched_send.called_once_with(
                    "!test:localhost", "opsdroid.dev", {"hello": "world"}
                )


@pytest.mark.asyncio
class TestEventCreatorMatrixAsync:
    """Basic setting up for tests"""

    connector = setup_connector()
    api = nio.AsyncClient("https://notaurl.com", None)
    connector.connection = api

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
            "age": 23394532373,
        }

    @property
    def encrypted_file_json(self):
        return {
            "origin_server_ts": 1534013434328,
            "sender": "@neo:matrix.org",
            "event_id": "$1534013434516721kIgMV:matrix.org",
            "content": {
                "body": "stereo_reproject.py",
                "info": {"mimetype": "text/x-python", "size": 1239},
                "msgtype": "m.file",
                "file": {
                    "v": "v2",
                    "key": {
                        "kty": "oct",
                        "alg": "A256CTR",
                        "ext": True,
                        "key_ops": ["encrypt", "decrypt"],
                        "k": "randomkey",
                    },
                    "iv": "randomiv",
                    "hashes": {"sha256": "shakey"},
                    "url": "mxc://matrix.org/vtgAIrGtuYJQCXNKRGhVfSMX",
                    "mimetype": "text/x-python",
                },
            },
            "room_id": "!MeRdFpEonLoCwhoHeT:matrix.org",
            "type": "m.room.message",
            "unsigned": {"age": 23394532373},
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
            "age": 2542608318,
        }

    @property
    def encrypted_image_json(self):
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
                    "thumbnail_file": {
                        "v": "v2",
                        "key": {
                            "kty": "oct",
                            "alg": "A256CTR",
                            "ext": True,
                            "key_ops": ["encrypt", "decrypt"],
                            "k": "randomkey",
                        },
                        "iv": "randomiv",
                        "hashes": {"sha256": "shakey"},
                        "url": "mxc://matrix.org/HjHqeJDDxcnOEGydCQlJZQwC",
                        "mimetype": "image/png",
                    },
                    "w": 1172,
                },
                "msgtype": "m.image",
                "file": {
                    "v": "v2",
                    "key": {
                        "kty": "oct",
                        "alg": "A256CTR",
                        "ext": True,
                        "key_ops": ["encrypt", "decrypt"],
                        "k": "randomkey",
                    },
                    "iv": "randomiv",
                    "hashes": {"sha256": "shakey"},
                    "url": "mxc://matrix.org/iDHKYJSQZZrrhOxAkMBMOaeo",
                    "mimetype": "image/png",
                },
            },
            "event_id": "$15548652221495790FYlHC:matrix.org",
            "origin_server_ts": 1554865222742,
            "room_id": "!MeRdFpEonLoCwhoHeT:matrix.org",
            "sender": "@neo:matrix.org",
            "type": "m.room.message",
            "unsigned": {"age": 2542608318},
            "age": 2542608318,
        }

    @property
    def room_name_json(self):
        return {
            "content": {"name": "Testing"},
            "type": "m.room.name",
            "unsigned": {
                "prev_sender": "@neo:matrix.org",
                "replaces_state": "$wzwL9bnZ3hQOIcOGzY5g55jYkFHMM6PmaGZ2n9w1IuY",
                "age": 122,
                "prev_content": {"name": "test"},
            },
            "origin_server_ts": 1575305934310,
            "state_key": "",
            "sender": "@neo:matrix.org",
            "event_id": "$3r_PWCT9Vurlv-OFleAsf5gEnoZd-LEGHY6AGqZ5tJg",
        }

    @property
    def room_description_json(self):
        return {
            "content": {"topic": "Hello world"},
            "type": "m.room.topic",
            "unsigned": {"age": 137},
            "origin_server_ts": 1575306720044,
            "state_key": "",
            "sender": "@neo:matrix.org",
            "event_id": "$bEg2XISusHMKLBw9b4lMNpB2r9qYoesp512rKvbo5LA",
        }

    @property
    def message_edit_json(self):
        return {
            "content": {
                "msgtype": "m.text",
                "m.new_content": {"msgtype": "m.text", "body": "hello"},
                "m.relates_to": {
                    "rel_type": "m.replace",
                    "event_id": "$15573463541827394vczPd:matrix.org",
                },
                "body": " * hello",
            },
            "type": "m.room.message",
            "unsigned": {"age": 80},
            "origin_server_ts": 1575307305885,
            "sender": "@neo:matrix.org",
            "event_id": "$E8qj6GjtrxfRIH1apJGzDu-duUF-8D19zFQv0k4q1eM",
        }

    @property
    def reaction_json(self):
        return {
            "content": {
                "m.relates_to": {
                    "rel_type": "m.annotation",
                    "event_id": "$MYO9kzuKrOwRdIfwumh2n2KfSBAYLifpK156nd0f_hY",
                    "key": "👍",
                }
            },
            "type": "m.reaction",
            "unsigned": {"age": 90},
            "origin_server_ts": 1575315194228,
            "sender": "@neo:matrix.org",
            "event_id": "$4KOPKFjdJ5urFGJdK4lnS-Fd3qcNWbPdR_rzSCZK_g0",
        }

    @property
    def reply_json(self):
        return {
            "type": "m.room.message",
            "sender": "@neo:matrix.org",
            "content": {
                "msgtype": "m.text",
                "body": "> <@morpheus:matrix.org> I just did it manually.\n\nhello",
                "format": "org.matrix.custom.html",
                "formatted_body": '<mx-reply><blockquote><a href="https://matrix.to/#/!sdhlkHsdskdkHG:matrix.org/$15573463541827394vczPd:matrix.org">In reply to</a> <a href="https://matrix.to/#/@morpheus:matrix.org">@morpheus:matrix.org</a><br>I just did it manually.</blockquote></mx-reply>hello',
                "m.relates_to": {
                    "m.in_reply_to": {"event_id": "$15573463541827394vczPd:matrix.org"}
                },
            },
            "event_id": "$15755082701541RchcK:matrix.org",
            "origin_server_ts": 1575508270019,
            "unsigned": {"age": 501, "transaction_id": "m1575508269677.3"},
        }

    @property
    def join_room_json(self):
        return {
            "content": {
                "avatar_url": "mxc://example.org/SEsfnsuifSDFSSEF",
                "displayname": "Alice Margatroid",
                "membership": "join",
            },
            "event_id": "$143273582443PhrSn:example.org",
            "origin_server_ts": 1432735824653,
            "room_id": "!jEsUZKDJdhlrceRyVU:example.org",
            "sender": "@example:example.org",
            "state_key": "@alice:example.org",
            "type": "m.room.member",
            "unsigned": {"age": 1234},
        }

    @property
    def event_creator(self):
        patched_get_nick = amock.MagicMock()
        patched_get_nick.return_value = asyncio.Future()
        patched_get_nick.return_value.set_result("Rabbit Hole")
        self.connector.get_nick = patched_get_nick

        return MatrixEventCreator(self.connector)

    async def test_create_message(self):
        event = await self.event_creator.create_event(self.message_json, "hello")
        assert isinstance(event, events.Message)
        assert event.text == "I just did it manually."
        assert event.user == "Rabbit Hole"
        assert event.user_id == "@neo:matrix.org"
        assert event.target == "hello"
        assert event.event_id == "$15573463541827394vczPd:matrix.org"
        assert event.raw_event == self.message_json

    async def test_create_file(self):
        event = await self.event_creator.create_event(self.file_json, "hello")
        encrypted_event = await self.event_creator.create_event(
            self.encrypted_file_json, "hello"
        )

        assert isinstance(event, events.File)
        assert isinstance(encrypted_event, events.File)
        assert (
            event.url
            == encrypted_event.url
            == "https://notaurl.com/_matrix/media/r0/download/matrix.org/vtgAIrGtuYJQCXNKRGhVfSMX"
        )
        assert event.user == encrypted_event.user == "Rabbit Hole"
        assert event.user_id == encrypted_event.user_id == "@neo:matrix.org"
        assert event.target == encrypted_event.target == "hello"
        assert (
            event.event_id
            == encrypted_event.event_id
            == "$1534013434516721kIgMV:matrix.org"
        )
        assert event.raw_event == self.file_json
        assert encrypted_event.raw_event == self.encrypted_file_json

    async def test_create_image(self):
        event = await self.event_creator.create_event(self.image_json, "hello")
        encrypted_event = await self.event_creator.create_event(
            self.encrypted_image_json, "hello"
        )
        assert isinstance(event, events.Image)
        assert (
            event.url
            == encrypted_event.url
            == "https://notaurl.com/_matrix/media/r0/download/matrix.org/iDHKYJSQZZrrhOxAkMBMOaeo"
        )
        assert event.user == encrypted_event.user == "Rabbit Hole"
        assert event.user_id == encrypted_event.user_id == "@neo:matrix.org"
        assert event.target == encrypted_event.target == "hello"
        assert (
            event.event_id
            == encrypted_event.event_id
            == "$15548652221495790FYlHC:matrix.org"
        )
        assert event.raw_event == self.image_json
        assert encrypted_event.raw_event == self.encrypted_image_json

    async def test_unsupported_type(self):
        json = self.message_json
        json["type"] = "wibble"
        event = await self.event_creator.create_event(json, "hello")
        assert isinstance(event, matrix_events.GenericMatrixRoomEvent)
        assert event.event_type == "wibble"
        assert "wibble" in repr(event)
        assert event.target in repr(event)
        assert str(event.content) in repr(event)

    async def test_unsupported_message_type(self):
        json = self.message_json
        json["content"]["msgtype"] = "wibble"
        event = await self.event_creator.create_event(json, "hello")
        assert isinstance(event, matrix_events.GenericMatrixRoomEvent)
        assert event.content["msgtype"] == "wibble"

    async def test_room_name(self):
        event = await self.event_creator.create_event(self.room_name_json, "hello")
        assert isinstance(event, events.RoomName)
        assert event.user == "Rabbit Hole"
        assert event.user_id == "@neo:matrix.org"
        assert event.event_id == "$3r_PWCT9Vurlv-OFleAsf5gEnoZd-LEGHY6AGqZ5tJg"
        assert event.raw_event == self.room_name_json

    async def test_room_description(self):
        event = await self.event_creator.create_event(
            self.room_description_json, "hello"
        )
        assert isinstance(event, events.RoomDescription)
        assert event.user == "Rabbit Hole"
        assert event.user_id == "@neo:matrix.org"
        assert event.event_id == "$bEg2XISusHMKLBw9b4lMNpB2r9qYoesp512rKvbo5LA"
        assert event.raw_event == self.room_description_json

    async def test_edited_message(self):
        with amock.patch(api_string.format("room_context")) as patched_send:
            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result(
                nio.RoomContextResponse(
                    event=nio.Event(source=self.message_json),
                    room_id="",
                    start="",
                    end="",
                    events_before=[],
                    events_after=[],
                    state=[],
                )
            )
            event = await self.event_creator.create_event(
                self.message_edit_json, "hello"
            )

        assert isinstance(event, events.EditedMessage)
        assert event.text == "hello"
        assert event.user == "Rabbit Hole"
        assert event.user_id == "@neo:matrix.org"
        assert event.target == "hello"
        assert event.event_id == "$E8qj6GjtrxfRIH1apJGzDu-duUF-8D19zFQv0k4q1eM"
        assert event.raw_event == self.message_edit_json

        assert isinstance(event.linked_event, events.Message)

    async def test_reaction(self):
        with amock.patch(api_string.format("room_context")) as patched_send:
            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result(
                nio.RoomContextResponse(
                    event=nio.Event(source=self.message_json),
                    room_id="",
                    start="",
                    end="",
                    events_before=[],
                    events_after=[],
                    state=[],
                )
            )
            event = await self.event_creator.create_event(self.reaction_json, "hello")

        assert isinstance(event, events.Reaction)
        assert event.emoji == "👍"
        assert event.user == "Rabbit Hole"
        assert event.user_id == "@neo:matrix.org"
        assert event.target == "hello"
        assert event.event_id == "$4KOPKFjdJ5urFGJdK4lnS-Fd3qcNWbPdR_rzSCZK_g0"
        assert event.raw_event == self.reaction_json

        assert isinstance(event.linked_event, events.Message)

    async def test_reply(self):
        with amock.patch(api_string.format("room_context")) as patched_send:
            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result(
                nio.RoomContextResponse(
                    event=nio.Event(source=self.message_json),
                    room_id="",
                    start="",
                    end="",
                    events_before=[],
                    events_after=[],
                    state=[],
                )
            )
            event = await self.event_creator.create_event(self.reply_json, "hello")

        assert isinstance(event, events.Reply)
        assert event.text == "hello"
        assert event.user == "Rabbit Hole"
        assert event.user_id == "@neo:matrix.org"
        assert event.target == "hello"
        assert event.event_id == "$15755082701541RchcK:matrix.org"
        assert event.raw_event == self.reply_json

        assert isinstance(event.linked_event, events.Message)

    async def test_create_joinroom(self):
        with amock.patch(api_string.format("room_context")) as patched_send:
            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result(
                nio.RoomContextResponse(
                    event=nio.Event(source=self.message_json),
                    room_id="",
                    start="",
                    end="",
                    events_before=[],
                    events_after=[],
                    state=[],
                )
            )

        event = await self.event_creator.create_event(self.join_room_json, "hello")
        assert isinstance(event, events.JoinRoom)
        assert event.user == "Rabbit Hole"
        assert event.user_id == "@example:example.org"
        assert event.target == "hello"
        assert event.event_id == "$143273582443PhrSn:example.org"
        assert event.raw_event == self.join_room_json

    @property
    def custom_json(self):
        return {
            "content": {"hello": "world"},
            "event_id": "$15573463541827394vczPd:localhost",
            "origin_server_ts": 1557346354253,
            "room_id": "!test:localhost",
            "sender": "@neo:matrix.org",
            "type": "opsdroid.dev",
            "unsigned": {"age": 48926251},
            "age": 48926251,
        }

    async def test_create_generic(self):
        event = await self.event_creator.create_event(self.custom_json, "hello")
        assert isinstance(event, matrix_events.GenericMatrixRoomEvent)
        assert event.user == "Rabbit Hole"
        assert event.user_id == "@neo:matrix.org"
        assert event.target == "hello"
        assert event.event_id == "$15573463541827394vczPd:localhost"
        assert event.raw_event == self.custom_json
        assert event.content == {"hello": "world"}
        assert event.event_type == "opsdroid.dev"

    @property
    def custom_state_json(self):
        return {
            "content": {"hello": "world"},
            "type": "wibble.opsdroid.dev",
            "unsigned": {"age": 137},
            "origin_server_ts": 1575306720044,
            "state_key": "",
            "sender": "@neo:matrix.org",
            "event_id": "$bEg2XISusHMKLBw9b4lMNpB2r9qYoesp512rKvbo5LA",
        }

    async def test_create_generic_state(self):
        event = await self.event_creator.create_event(self.custom_state_json, "hello")
        assert isinstance(event, matrix_events.MatrixStateEvent)
        assert event.user == "Rabbit Hole"
        assert event.user_id == "@neo:matrix.org"
        assert event.target == "hello"
        assert event.event_id == "$bEg2XISusHMKLBw9b4lMNpB2r9qYoesp512rKvbo5LA"
        assert event.raw_event == self.custom_state_json
        assert event.content == {"hello": "world"}
        assert event.event_type == "wibble.opsdroid.dev"
        assert event.state_key == ""
