"""Tests for the ConnectorMatrix class."""
import asyncio
from copy import deepcopy

import aiohttp

import asynctest.mock as amock

import nio
import pytest

import opsdroid.connector.matrix.events as matrix_events
from opsdroid.core import OpsDroid
from opsdroid import events
from opsdroid.connector.matrix.connector import ConnectorMatrix, MatrixException
from opsdroid.connector.matrix.create_events import MatrixEventCreator
from opsdroid.cli.start import configure_lang  # noqa

api_string = "nio.AsyncClient.{}"


@pytest.fixture
def connector():
    """Initiate a basic connector setup for testing on"""
    connector = ConnectorMatrix(
        {
            "rooms": {"main": "#test:localhost"},
            "mxid": "@opsdroid:localhost",
            "password": "hello",
            "homeserver": "http://localhost:8008",
            "enable_encryption": True,
        }
    )
    api = nio.AsyncClient("https://notaurl.com", None)
    connector.connection = api

    return connector


@pytest.mark.asyncio
class TestConnectorMatrixAsync:
    """Test the async methods of the opsdroid Matrix connector class."""

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

    async def test_make_filter(self, connector):
        with amock.patch(api_string.format("send")) as patched_filter:

            connect_response = amock.Mock()
            connect_response.status = 200
            connect_response.json = amock.CoroutineMock()
            connect_response.json.return_value = {"filter_id": 10}

            connector.connection.token = "abc"

            patched_filter.return_value = asyncio.Future()
            patched_filter.return_value.set_result(connect_response)

            filter_id = await connector.make_filter(
                connector.connection, self.filter_json
            )

            assert filter_id == 10
            assert patched_filter.called

    async def test_exchange_keys(self, mocker, connector):

        connector.room_ids = {"main": "!aroomid:localhost"}

        patched_send_to_device = mocker.patch(
            api_string.format("send_to_device_messages"), return_value=asyncio.Future()
        )
        patched_send_to_device.return_value.set_result(None)

        mocker.patch(api_string.format("should_upload_keys"), return_value=True)
        patched_keys_upload = mocker.patch(
            api_string.format("keys_upload"), return_value=asyncio.Future()
        )
        patched_keys_upload.return_value.set_result(None)

        mocker.patch(api_string.format("should_query_keys"), return_value=True)
        patched_keys_query = mocker.patch(
            api_string.format("keys_query"), return_value=asyncio.Future()
        )
        patched_keys_query.return_value.set_result(None)

        mocker.patch(api_string.format("should_claim_keys"), return_value=True)
        patched_keys_claim = mocker.patch(
            api_string.format("keys_claim"), return_value=asyncio.Future()
        )
        patched_keys_claim.return_value.set_result(None)

        patched_missing_sessions = mocker.patch(
            api_string.format("get_missing_sessions"), return_value=None
        )

        await connector.exchange_keys(initial_sync=True)

        assert patched_send_to_device.called
        assert patched_keys_upload.called
        assert patched_keys_query.called
        patched_keys_claim.assert_called_once_with(patched_missing_sessions())

        patched_get_users = mocker.patch(
            api_string.format("get_users_for_key_claiming"), return_value=None
        )

        await connector.exchange_keys(initial_sync=False)

        assert patched_send_to_device.called
        assert patched_keys_upload.called
        assert patched_keys_query.called
        patched_keys_claim.assert_called_with(patched_get_users())

    async def test_get_formatted_message_body(self, connector):
        original_html = "<p><h3><no>Hello World</no></h3></p>"
        original_body = "### Hello World"
        message = connector._get_formatted_message_body(original_html)
        assert message["formatted_body"] == "<h3>Hello World</h3>"
        assert message["body"] == "Hello World"

        message = connector._get_formatted_message_body(original_html, original_body)
        assert message["formatted_body"] == "<h3>Hello World</h3>"
        assert message["body"] == "### Hello World"

    async def _get_message(self, connector):
        connector.room_ids = {"main": "!aroomid:localhost"}
        connector.filter_id = "arbitrary string"
        m = "opsdroid.connector.matrix.ConnectorMatrix.get_nick"

        with amock.patch(m) as patched_nick:
            patched_nick.return_value = asyncio.Future()
            patched_nick.return_value.set_result("Neo")

            async for x in connector._parse_sync_response(self.sync_return):
                return x

    async def test_send_edited_message(self, connector):
        message = events.EditedMessage(
            text="New message",
            target="!test:localhost",
            linked_event=events.Message("hello", event_id="$hello"),
            connector=connector,
        )

        def expected_content(message):
            new_content = connector._get_formatted_message_body(message.text)
            event_id = (
                message.linked_event
                if isinstance(message.linked_event, str)
                else message.linked_event.event_id
            )
            return {
                "msgtype": "m.text",
                "m.new_content": new_content,
                "body": f"* {new_content['body']}",
                "m.relates_to": {"rel_type": "m.replace", "event_id": event_id},
            }

        with amock.patch(
            api_string.format("room_send")
        ) as patched_send, OpsDroid() as _:
            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result({})

            await connector.send(message)

            patched_send.assert_called_once_with(
                message.target,
                "m.room.message",
                expected_content(message),
                ignore_unverified_devices=True,
            )

            # Test linked event as event id
            message.linked_event = "$hello"

            await connector.send(message)

            patched_send.assert_called_with(
                message.target,
                "m.room.message",
                expected_content(message),
                ignore_unverified_devices=True,
            )

            # Test responding to an edit
            edited_message = events.EditedMessage("hello")
            await message.respond(edited_message)

            patched_send.assert_called_with(
                message.target,
                "m.room.message",
                expected_content(edited_message),
                ignore_unverified_devices=True,
            )

    async def test_respond_retry(self, connector):
        message = await self._get_message(connector)
        with amock.patch(api_string.format("room_send")) as patched_send:
            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result(None)
            await connector.send(message)

            message_obj = connector._get_formatted_message_body(message.text)
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

            await connector.send(message)

            message_obj = connector._get_formatted_message_body(message.text)
            patched_send.assert_called_with(
                message.target,
                "m.room.message",
                message_obj,
                ignore_unverified_devices=True,
            )

    async def test_respond_room(self, connector):
        message = await self._get_message(connector)
        with amock.patch(api_string.format("room_send")) as patched_send:

            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result(None)

            message.target = "main"
            await connector.send(message)

            message_obj = connector._get_formatted_message_body(message.text)
            patched_send.assert_called_once_with(
                "!aroomid:localhost",
                "m.room.message",
                message_obj,
                ignore_unverified_devices=True,
            )

    async def test_disconnect(self, mocker, connector):
        patched_close = mocker.patch(
            api_string.format("close"), return_value=asyncio.Future()
        )
        patched_close.return_value.set_result(None)

        await connector.disconnect()
        assert patched_close.called

    def test_get_roomname(self, connector):
        connector.rooms = {
            "main": {"alias": "#notthisroom:localhost"},
            "test": {"alias": "#thisroom:localhost"},
        }
        connector.room_ids = dict(
            zip(
                connector.rooms.keys(),
                ["!aroomid:localhost", "!anotherroomid:localhost"],
            )
        )

        assert connector.get_roomname("#thisroom:localhost") == "test"
        assert connector.get_roomname("!aroomid:localhost") == "main"
        assert connector.get_roomname("someroom") == "someroom"

    def test_lookup_target(self, connector):
        connector.room_ids = {"main": "!aroomid:localhost", "test": "#test:localhost"}

        assert connector.lookup_target("main") == "!aroomid:localhost"
        assert connector.lookup_target("#test:localhost") == "!aroomid:localhost"
        assert connector.lookup_target("!aroomid:localhost") == "!aroomid:localhost"

    async def test_respond_image(self, mocker, caplog, connector):
        gif_bytes = (
            b"GIF89a\x01\x00\x01\x00\x00\xff\x00,"
            b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;"
        )

        image = events.Image(file_bytes=gif_bytes, target="!test:localhost")

        patched_send = mocker.patch(
            api_string.format("room_send"), return_value=asyncio.Future()
        )
        patched_send.return_value.set_result(None)

        connector.connection.store = mocker.MagicMock()
        connector.connection.store.load_encrypted_rooms.return_value = []

        patched_upload = mocker.patch(
            api_string.format("upload"), return_value=asyncio.Future()
        )
        patched_upload.return_value.set_result([nio.UploadResponse("mxc://aurl"), None])

        await connector.send(image)

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

        connector.connection.store.load_encrypted_rooms.return_value = [
            "!test:localhost"
        ]
        patched_upload.return_value = asyncio.Future()
        patched_upload.return_value.set_result(
            [nio.UploadResponse("mxc://aurl"), file_dict]
        )

        await connector.send(image)

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
        connector.connection.store.load_encrypted_rooms.return_value = []
        patched_upload.return_value = asyncio.Future()
        patched_upload.return_value.set_result(
            [nio.UploadError(message=error_message, status_code=error_code), None]
        )

        caplog.clear()
        await connector.send(image)
        assert [
            f"Error while sending the file. Reason: {error_message} (status code {error_code})"
        ] == [rec.message for rec in caplog.records]

    async def test_respond_mxc(self, connector):
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
            await connector.send(image)

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

    async def test_respond_file(self, mocker, connector):
        file_event = events.File(
            file_bytes=b"aslkdjlaksdjlkajdlk",
            target="!test:localhost",
            mimetype="text/plain",
        )

        patched_send = mocker.patch(
            api_string.format("room_send"), return_value=asyncio.Future()
        )
        patched_send.return_value.set_result(None)

        connector.connection.store = mocker.MagicMock()
        connector.connection.store.load_encrypted_rooms.return_value = []

        patched_upload = mocker.patch(
            api_string.format("upload"), return_value=asyncio.Future()
        )
        patched_upload.return_value.set_result([nio.UploadResponse("mxc://aurl"), None])

        await connector.send(file_event)

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

        connector.connection.store.load_encrypted_rooms.return_value = [
            "!test:localhost"
        ]
        patched_upload.return_value = asyncio.Future()
        patched_upload.return_value.set_result(
            [nio.UploadResponse("mxc://aurl"), file_dict]
        )

        await connector.send(file_event)

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

    async def test_respond_new_room(self, caplog, connector):
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

            resp = await connector.send(event)
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
            resp = await connector.send(event)
            assert [
                f"Error while creating the room. Reason: {error_message} (status code {error_code})"
            ] == [rec.message for rec in caplog.records]

    async def test_respond_room_address(self, connector):
        event = events.RoomAddress("#test:localhost", target="!test:localhost")

        with amock.patch(api_string.format("room_put_state")) as patched_send:
            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result({})

            await connector.send(event)

            assert patched_send.called_once_with("!test:localhost", "#test:localhost")

    async def test_respond_join_room(self, connector):
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
            await connector.send(event)
            assert patched_send.called_once_with("#test:localhost")

    async def test_respond_join_room_error(self, caplog, connector):
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
            await connector.send(event)
            assert patched_send.called_once_with("#test:localhost")
            assert patched_get_room_id.called_once_with("#test:localhost")
            assert [
                f"Error resolving room id for #test:localhost: {error_message} (status code {error_code})"
            ] == [rec.message for rec in caplog.records]

    async def test_respond_user_invite(self, connector):
        event = events.UserInvite("@test:localhost", target="!test:localhost")
        with amock.patch(api_string.format("room_invite")) as patched_send:
            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result({})
            await connector.send(event)
            assert patched_send.called_once_with("#test:localhost", "@test:localhost")

    async def test_respond_room_description(self, connector):
        event = events.RoomDescription("A test room", target="!test:localhost")

        with amock.patch(api_string.format("room_put_state")) as patched_send:
            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result({})
            await connector.send(event)
            assert patched_send.called_once_with("#test:localhost", "A test room")

    async def test_respond_room_image(self, connector):
        image = events.Image(url="mxc://aurl")
        event = events.RoomImage(image, target="!test:localhost")

        with OpsDroid() as opsdroid, amock.patch(
            api_string.format("room_put_state")
        ) as patched_send:
            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result({})
            opsdroid.connectors = [connector]
            await connector.send(event)
            assert patched_send.called_once_with(
                "#test:localhost",
                "m.room.avatar",
                {"url": "mxc://aurl"},
                state_key=None,
                ignore_unverified_devices=True,
            )

    async def test_respond_user_role(self, connector):
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
                    opsdroid.connectors = [connector]

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

                    await connector.send(event)

                    modified_power_levels = deepcopy(existing_power_levels)
                    modified_power_levels["users"]["@test:localhost"] = pl

                    assert patched_send.called_once_with(
                        "!test:localhost",
                        "m.room.power_levels",
                        existing_power_levels,
                        state_key=None,
                    )

    async def test_send_reaction(self, connector):
        message = events.Message(
            "hello", event_id="$11111", connector=connector, target="!test:localhost"
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

    async def test_send_reply(self, connector):
        message = events.Message(
            "hello", event_id="$11111", connector=connector, target="!test:localhost"
        )
        reply = events.Reply("reply")
        with OpsDroid() as _:
            with amock.patch(api_string.format("room_send")) as patched_send:
                patched_send.return_value = asyncio.Future()
                patched_send.return_value.set_result(None)

                await message.respond(reply)

                content = connector._get_formatted_message_body(
                    reply.text, msgtype="m.text"
                )

                content["m.relates_to"] = {
                    "m.in_reply_to": {"event_id": message.event_id}
                }

                assert patched_send.called_once_with(
                    "!test:localhost", "m.room.message", content
                )

    async def test_send_reply_id(self, connector):
        reply = events.Reply("reply", linked_event="$hello", target="!hello:localhost")
        with OpsDroid() as _:
            with amock.patch(api_string.format("room_send")) as patched_send:
                patched_send.return_value = asyncio.Future()
                patched_send.return_value.set_result(None)

                await connector.send(reply)

                content = connector._get_formatted_message_body(
                    reply.text, msgtype="m.text"
                )

                content["m.relates_to"] = {"m.in_reply_to": {"event_id": "$hello"}}

                assert patched_send.called_once_with(
                    "!test:localhost", "m.room.message", content
                )

    async def test_alias_already_exists(self, caplog, connector):

        with amock.patch(api_string.format("room_put_state")) as patched_alias:
            patched_alias.return_value = asyncio.Future()
            patched_alias.return_value.set_result(
                nio.RoomPutStateResponse(event_id="some_id", room_id="!test:localhost")
            )

            resp = await connector._send_room_address(
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
            with pytest.raises(MatrixException):
                resp = await connector._send_room_address(
                    events.RoomAddress(target="!test:localhost", address="hello")
                )

            error_code = 409
            patched_alias.return_value = asyncio.Future()
            patched_alias.return_value.set_result(
                nio.RoomPutStateError(message=error_message, status_code=error_code)
            )
            resp = await connector._send_room_address(
                events.RoomAddress(target="!test:localhost", address="hello")
            )
            assert ["A room with the alias hello already exists."] == [
                rec.message for rec in caplog.records
            ]

    async def test_user_invite_unknown_error(self, caplog, connector):
        with amock.patch(api_string.format("room_invite")) as patched_invite:

            patched_invite.return_value = asyncio.Future()
            patched_invite.return_value.set_result(
                nio.RoomInviteError(
                    message="@neo.matrix.org is already in the room", status_code=400
                )
            )

            with pytest.raises(MatrixException) as exc:
                await connector._send_user_invitation(
                    events.UserInvite(
                        target="!test:localhost", user_id="@neo:matrix.org"
                    )
                )
                assert exc.nio_error.message == "@neo.matrix.org is already in the room"

    async def test_already_in_room_warning(self, caplog, connector):
        with amock.patch(api_string.format("room_invite")) as patched_invite:

            patched_invite.return_value = asyncio.Future()
            patched_invite.return_value.set_result(
                nio.RoomInviteError(
                    message="@neo.matrix.org is already in the room", status_code=403
                )
            )
            await connector._send_user_invitation(
                events.UserInvite(target="!test:localhost", user_id="@neo:matrix.org")
            )
            assert ["@neo:matrix.org is already in the room, ignoring."] == [
                rec.message for rec in caplog.records
            ]

    async def test_invalid_role(self, connector):
        with pytest.raises(ValueError):
            await connector._set_user_role(
                events.UserRole(
                    "wibble", target="!test:localhost", user_id="@test:localhost"
                )
            )

    async def test_no_user_id(self, connector):
        with pytest.raises(ValueError):
            await connector._set_user_role(
                events.UserRole("wibble", target="!test:localhost")
            )

    def test_m_notice(self, connector):
        connector.rooms["test"] = {"alias": "#test:localhost", "send_m_notice": True}

        assert connector.message_type("main") == "m.text"
        assert connector.message_type("test") == "m.notice"
        connector.send_m_notice = True
        assert connector.message_type("main") == "m.notice"

        # Reset the state
        connector.send_m_notice = False
        del connector.rooms["test"]

    def test_construct(self, connector):
        jr = matrix_events.MatrixJoinRules("hello")
        assert jr.content["join_rule"] == "hello"

        hv = matrix_events.MatrixHistoryVisibility("hello")
        assert hv.content["history_visibility"] == "hello"

    async def test_send_generic_event(self, connector):
        event = matrix_events.GenericMatrixRoomEvent(
            "opsdroid.dev", {"hello": "world"}, target="!test:localhost"
        )
        with OpsDroid() as _:
            with amock.patch(api_string.format("room_send")) as patched_send:
                patched_send.return_value = asyncio.Future()
                patched_send.return_value.set_result(None)

                await connector.send(event)
                assert patched_send.called_once_with(
                    "!test:localhost", "opsdroid.dev", {"hello": "world"}
                )


@pytest.mark.asyncio
class TestEventCreatorMatrixAsync:
    """Basic setting up for tests"""

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

    @pytest.fixture
    def event_creator(self, connector):
        patched_get_nick = amock.MagicMock()
        patched_get_nick.return_value = asyncio.Future()
        patched_get_nick.return_value.set_result("Rabbit Hole")
        connector.get_nick = patched_get_nick

        return MatrixEventCreator(connector)

    async def test_create_message(self, connector, event_creator):
        event = await event_creator.create_event(self.message_json, "hello")
        assert isinstance(event, events.Message)
        assert event.text == "I just did it manually."
        assert event.user == "Rabbit Hole"
        assert event.user_id == "@neo:matrix.org"
        assert event.target == "hello"
        assert event.event_id == "$15573463541827394vczPd:matrix.org"
        assert event.raw_event == self.message_json

    async def test_create_file(self, connector, event_creator):
        event = await event_creator.create_event(self.file_json, "hello")
        encrypted_event = await event_creator.create_event(
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

    async def test_create_image(self, connector, event_creator):
        event = await event_creator.create_event(self.image_json, "hello")
        encrypted_event = await event_creator.create_event(
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

    async def test_unsupported_type(self, connector, event_creator):
        json = self.message_json
        json["type"] = "wibble"
        event = await event_creator.create_event(json, "hello")
        assert isinstance(event, matrix_events.GenericMatrixRoomEvent)
        assert event.event_type == "wibble"
        assert "wibble" in repr(event)
        assert event.target in repr(event)
        assert str(event.content) in repr(event)

    async def test_unsupported_message_type(self, connector, event_creator):
        json = self.message_json
        json["content"]["msgtype"] = "wibble"
        event = await event_creator.create_event(json, "hello")
        assert isinstance(event, matrix_events.GenericMatrixRoomEvent)
        assert event.content["msgtype"] == "wibble"

    async def test_room_name(self, connector, event_creator):
        event = await event_creator.create_event(self.room_name_json, "hello")
        assert isinstance(event, events.RoomName)
        assert event.user == "Rabbit Hole"
        assert event.user_id == "@neo:matrix.org"
        assert event.event_id == "$3r_PWCT9Vurlv-OFleAsf5gEnoZd-LEGHY6AGqZ5tJg"
        assert event.raw_event == self.room_name_json

    async def test_room_description(self, connector, event_creator):
        event = await event_creator.create_event(self.room_description_json, "hello")
        assert isinstance(event, events.RoomDescription)
        assert event.user == "Rabbit Hole"
        assert event.user_id == "@neo:matrix.org"
        assert event.event_id == "$bEg2XISusHMKLBw9b4lMNpB2r9qYoesp512rKvbo5LA"
        assert event.raw_event == self.room_description_json

    async def test_edited_message(self, connector, event_creator):
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
            event = await event_creator.create_event(self.message_edit_json, "hello")

        assert isinstance(event, events.EditedMessage)
        assert event.text == "hello"
        assert event.user == "Rabbit Hole"
        assert event.user_id == "@neo:matrix.org"
        assert event.target == "hello"
        assert event.event_id == "$E8qj6GjtrxfRIH1apJGzDu-duUF-8D19zFQv0k4q1eM"
        assert event.raw_event == self.message_edit_json

        assert isinstance(event.linked_event, events.Message)

    async def test_reaction(self, connector, event_creator):
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
            event = await event_creator.create_event(self.reaction_json, "hello")

        assert isinstance(event, events.Reaction)
        assert event.emoji == "👍"
        assert event.user == "Rabbit Hole"
        assert event.user_id == "@neo:matrix.org"
        assert event.target == "hello"
        assert event.event_id == "$4KOPKFjdJ5urFGJdK4lnS-Fd3qcNWbPdR_rzSCZK_g0"
        assert event.raw_event == self.reaction_json

        assert isinstance(event.linked_event, events.Message)

    async def test_reply(self, connector, event_creator):
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
            event = await event_creator.create_event(self.reply_json, "hello")

        assert isinstance(event, events.Reply)
        assert event.text == "hello"
        assert event.user == "Rabbit Hole"
        assert event.user_id == "@neo:matrix.org"
        assert event.target == "hello"
        assert event.event_id == "$15755082701541RchcK:matrix.org"
        assert event.raw_event == self.reply_json

        assert isinstance(event.linked_event, events.Message)

    async def test_create_joinroom(self, connector, event_creator):
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

        event = await event_creator.create_event(self.join_room_json, "hello")
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

    async def test_create_generic(self, connector, event_creator):
        event = await event_creator.create_event(self.custom_json, "hello")
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

    async def test_create_generic_state(self, connector, event_creator):
        event = await event_creator.create_event(self.custom_state_json, "hello")
        assert isinstance(event, matrix_events.MatrixStateEvent)
        assert event.user == "Rabbit Hole"
        assert event.user_id == "@neo:matrix.org"
        assert event.target == "hello"
        assert event.event_id == "$bEg2XISusHMKLBw9b4lMNpB2r9qYoesp512rKvbo5LA"
        assert event.raw_event == self.custom_state_json
        assert event.content == {"hello": "world"}
        assert event.event_type == "wibble.opsdroid.dev"
        assert event.state_key == ""
