"""Connector for Matrix (https://matrix.org)."""
import functools
import json
import logging
import re
from pathlib import Path
from urllib.parse import urlparse

import aiohttp
import nio
import nio.responses
import nio.exceptions

from opsdroid import const, events
from opsdroid.connector import Connector, register_event
from voluptuous import Required

from . import events as matrixevents
from .create_events import MatrixEventCreator
from .html_cleaner import clean

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = {
    Required("mxid"): str,
    Required("password"): str,
    Required("rooms"): dict,
    "homeserver": str,
    "nick": str,
    "room_specific_nicks": bool,
    "device_name": str,
    "device_id": str,
    "store_path": str,
    "enable_encryption": bool,
}

__all__ = ["ConnectorMatrix"]


class MatrixException(Exception):
    """Wrap a matrix-nio Error in an Exception so it can raised."""

    def __init__(self, nio_error):
        self.nio_error = nio_error


def ensure_room_id_and_send(func):
    """
    Ensure that the target for the event is a matrix room id.

    Also retry the function call if the server disconnects.
    """

    @functools.wraps(func)
    async def ensure_room_id(self, event):
        if not event.target.startswith(("!", "#")):
            event.target = self.room_ids[event.target]

        if not event.target.startswith("!"):
            response = await self.connection.room_resolve_alias(event.target)
            if isinstance(response, nio.RoomResolveAliasError):
                _LOGGER.error(
                    f"Error resolving room id for {event.target}: {response.message} (status code {response.status_code})"
                )
            else:
                event.target = response.room_id

        try:
            return_val = await func(self, event)
        except aiohttp.client_exceptions.ServerDisconnectedError:
            _LOGGER.debug(_("Server had disconnected, retrying send."))
            return_val = await func(self, event)

        # If the send call returns a matrix-nio error then we raise it
        if isinstance(return_val, nio.responses.ErrorResponse):
            raise MatrixException(return_val)

        return return_val

    return ensure_room_id


class ConnectorMatrix(Connector):
    """Connector for Matrix (https://matrix.org)."""

    def __init__(self, config, opsdroid=None):  # noqa: D107
        """Init the config for the connector."""
        super().__init__(config, opsdroid=opsdroid)

        self.name = "matrix"  # The name of your connector
        self.rooms = self._process_rooms_dict(config["rooms"])
        self.room_ids = {}
        self.default_target = self.rooms["main"]["alias"]
        self.mxid = config["mxid"]
        self.nick = config.get("nick")
        self.homeserver = config.get("homeserver", "https://matrix.org")
        self.password = config["password"]
        self.room_specific_nicks = config.get("room_specific_nicks", False)
        self.send_m_notice = config.get("send_m_notice", False)
        self.session = None
        self.filter_id = None
        self.connection = None
        self.device_name = config.get("device_name", "opsdroid")
        self.device_id = config.get("device_id", "opsdroid")
        self.store_path = config.get(
            "store_path", str(Path(const.DEFAULT_ROOT_PATH, "matrix"))
        )
        self._ignore_unverified = True
        self._allow_encryption = config.get("enable_encryption", False)
        if (
            self._allow_encryption and not nio.crypto.ENCRYPTION_ENABLED
        ):  # pragma: no cover
            _LOGGER.warning(
                "enable_encryption is True but encryption support is not available."
            )
            self._allow_encryption = False

        self._event_creator = MatrixEventCreator(self)

    def message_type(self, room):
        """Subtype to use to send into a specific room."""
        if self.send_m_notice:
            return "m.notice"
        reverse_room_ids = {v: k for k, v in self.room_ids.items()}
        room = reverse_room_ids.get(room, room)
        if room in self.rooms:
            if self.rooms[room].get("send_m_notice", False):
                return "m.notice"

        return "m.text"

    def _process_rooms_dict(self, rooms):
        out_rooms = {}
        for name, room in rooms.items():
            if isinstance(room, str):
                room = {"alias": room}
            out_rooms[name] = room
        return out_rooms

    @property
    def filter_json(self):
        """Define JSON filter to apply to incoming events."""
        return json.dumps(
            {
                "event_format": "client",
                "account_data": {"limit": 0, "types": []},
                "presence": {"limit": 0, "types": []},
                "room": {
                    "account_data": {"types": []},
                    "ephemeral": {"types": []},
                    "state": {"types": []},
                },
            }
        )

    async def make_filter(self, api, fjson):
        """Make a filter on the server for future syncs."""
        path = f"/_matrix/client/r0/user/{self.mxid}/filter"
        headers = {"Authorization": f"Bearer {api.token}"}
        resp = await api.send(method="post", path=path, data=fjson, headers=headers)

        resp_json = await resp.json()
        return int(resp_json["filter_id"])

    async def exchange_keys(self, initial_sync=False):
        """Send to-device messages and perform key exchange operations."""
        await self.connection.send_to_device_messages()
        if self.connection.should_upload_keys:
            await self.connection.keys_upload()
        if self.connection.should_query_keys:
            await self.connection.keys_query()

        if initial_sync:
            for room_id in self.room_ids.values():
                try:
                    await self.connection.keys_claim(
                        self.connection.get_missing_sessions(room_id)
                    )
                except nio.LocalProtocolError:
                    continue
        elif self.connection.should_claim_keys:
            await self.connection.keys_claim(
                self.connection.get_users_for_key_claiming()
            )

    async def connect(self):
        """Create connection object with chat library."""

        if self._allow_encryption:
            _LOGGER.debug(f"Using {self.store_path} for the matrix client store.")
            Path(self.store_path).mkdir(exist_ok=True)

        config = nio.AsyncClientConfig(
            encryption_enabled=self._allow_encryption,
            pickle_key="",
            store_name="opsdroid.db" if self._allow_encryption else "",
        )
        mapi = nio.AsyncClient(
            self.homeserver,
            self.mxid,
            config=config,
            store_path=self.store_path if self._allow_encryption else "",
            device_id=self.device_id,
        )

        login_response = await mapi.login(
            password=self.password, device_name=self.device_name
        )
        if isinstance(login_response, nio.LoginError):
            _LOGGER.error(
                f"Error while connecting: {login_response.message} (status code {login_response.status_code})"
            )
            return

        mapi.token = login_response.access_token
        mapi.sync_token = None

        for roomname, room in self.rooms.items():
            response = await mapi.join(room["alias"])
            if isinstance(response, nio.JoinError):
                _LOGGER.error(
                    f"Error while joining room: {room['alias']}, Message: {response.message} (status code {response.status_code})"
                )

            else:
                self.room_ids[roomname] = response.room_id

        self.connection = mapi

        # Create a filter now, saves time on each later sync
        self.filter_id = await self.make_filter(mapi, self.filter_json)
        first_filter_id = await self.make_filter(
            mapi, '{ "room": { "timeline" : { "limit" : 1 } } }'
        )

        # Do initial sync so we don't get old messages later.
        response = await self.connection.sync(
            timeout=3000, sync_filter=first_filter_id, full_state=True
        )

        if isinstance(response, nio.SyncError):
            _LOGGER.error(
                f"Error during initial sync: {response.message} (status code {response.status_code})"
            )
            return

        self.connection.sync_token = response.next_batch

        await self.exchange_keys(initial_sync=True)

        if self.nick:
            display_name = await self.connection.get_displayname(self.mxid)
            if display_name != self.nick:
                await self.connection.set_displayname(self.nick)

    async def disconnect(self):
        """Close the matrix session."""
        await self.connection.close()

    async def _parse_sync_response(self, response):
        self.connection.sync_token = response.next_batch

        # Emit Invite events for every room in the invite list.
        for roomid, roomInfo in response.rooms.invite.items():
            # Process the invite list to extract the person who invited us.
            invite_event = [
                e
                for e in roomInfo.invite_state
                if isinstance(e, nio.InviteMemberEvent)
                if e.membership == "invite"
            ][0]
            sender = await self.get_nick(None, invite_event.sender)

            await self.opsdroid.parse(
                events.UserInvite(
                    target=roomid,
                    user_id=invite_event.sender,
                    user=sender,
                    connector=self,
                    raw_event=invite_event,
                )
            )

        for roomid, roomInfo in response.rooms.join.items():
            if roomInfo.timeline:
                for event in roomInfo.timeline.events:
                    if event.sender != self.mxid:
                        if event.source["type"] == "m.room.member":
                            event.source["content"] = event.content
                        if isinstance(event, nio.MegolmEvent):
                            try:  # pragma: no cover
                                event = self.connection.decrypt_event(event)
                            except nio.exceptions.EncryptionError:  # pragma: no cover
                                _LOGGER.exception(f"Failed to decrypt event {event}")
                        return await self._event_creator.create_event(
                            event.source, roomid
                        )

    async def listen(self):  # pragma: no cover
        """Listen for new messages from the chat service."""
        while True:  # pylint: disable=R1702
            response = await self.connection.sync(
                timeout=int(60 * 1e3),  # 1m in ms
                sync_filter=self.filter_id,
                since=self.connection.sync_token,
            )
            if isinstance(response, nio.SyncError):
                _LOGGER.error(
                    f"Error during sync: {response.message} (status code {response.status_code})"
                )
                continue

            _LOGGER.debug(_("Matrix sync request returned."))

            await self.exchange_keys()

            message = await self._parse_sync_response(response)

            if message:
                await self.opsdroid.parse(message)

    def lookup_target(self, room):
        """Convert name or alias of a room to the corresponding room ID."""
        room = self.get_roomname(room)
        return self.room_ids.get(room, room)

    async def get_nick(self, roomid, mxid):
        """
        Get nickname from user ID.

        Get the nickname of a sender depending on the room specific config
        setting.
        """
        if self.room_specific_nicks and roomid is not None:

            res = await self.connection.joined_members(roomid)
            if isinstance(res, nio.JoinedMembersError):
                logging.exception("Failed to lookup room members for %s.", roomid)
                # fallback to global profile
            else:
                for member in res.members:
                    if member.user_id == mxid:
                        return member.display_name
                return mxid

        res = await self.connection.get_displayname(mxid)
        if isinstance(res, nio.ProfileGetDisplayNameError):
            _LOGGER.error("Failed to lookup nick for %s.", mxid)
            return mxid
        if res.displayname is None:
            return mxid
        return res.displayname

    def get_roomname(self, room):
        """Get the name of a room from alias or room ID."""
        if room.startswith(("#", "!")):
            for room_name, room_alias in self.rooms.items():
                room_alias = room_alias["alias"]
                if room in (room_alias, self.room_ids[room_name]):
                    return room_name

        return room

    @staticmethod
    def _get_formatted_message_body(message, body=None, msgtype="m.text"):
        """
        Get HTML from a message.

        Return the json representation of the message in
        "org.matrix.custom.html" format.
        """
        # Markdown leaves a <p></p> around standard messages that we want to
        # strip:
        if message.startswith("<p>"):
            message = message[3:]
            if message.endswith("</p>"):
                message = message[:-4]

        clean_html = clean(message)

        return {
            # Strip out any tags from the markdown to make the body
            "body": body if body else re.sub("<[^<]+?>", "", clean_html),
            "msgtype": msgtype,
            "format": "org.matrix.custom.html",
            "formatted_body": clean_html,
        }

    @register_event(events.Message)
    @ensure_room_id_and_send
    async def _send_message(self, message):
        """Send `message.text` back to the chat service."""
        return await self.connection.room_send(
            message.target,
            "m.room.message",
            self._get_formatted_message_body(
                message.text, msgtype=self.message_type(message.target)
            ),
            ignore_unverified_devices=self._ignore_unverified,
        )

    @register_event(events.EditedMessage)
    @ensure_room_id_and_send
    async def _send_edit(self, message):
        if isinstance(message.linked_event, events.EditedMessage):
            # If we are attempting to edit an edit, move up the tree and then
            # try again.
            message.linked_event = message.linked_event.linked_event
            return await self._send_edit(message)
        elif isinstance(message.linked_event, str):
            edited_event_id = message.linked_event
        else:
            edited_event_id = message.linked_event.event_id

        new_content = self._get_formatted_message_body(
            message.text, msgtype=self.message_type(message.target)
        )

        content = {
            "msgtype": self.message_type(message.target),
            "m.new_content": new_content,
            "body": f"* {new_content['body']}",
            "m.relates_to": {"rel_type": "m.replace", "event_id": edited_event_id},
        }

        return await self.connection.room_send(
            message.target,
            "m.room.message",
            content,
            ignore_unverified_devices=self._ignore_unverified,
        )

    @register_event(events.Reply)
    @ensure_room_id_and_send
    async def _send_reply(self, reply):
        if isinstance(reply.linked_event, str):
            reply_event_id = reply.linked_event
        else:
            reply_event_id = reply.linked_event.event_id

        # TODO: Insert reply fallback here
        content = self._get_formatted_message_body(
            reply.text, msgtype=self.message_type(reply.target)
        )

        content["m.relates_to"] = {"m.in_reply_to": {"event_id": reply_event_id}}

        return await self.connection.room_send(
            reply.target,
            "m.room.message",
            content,
            ignore_unverified_devices=self._ignore_unverified,
        )

    @register_event(events.Reaction)
    @ensure_room_id_and_send
    async def _send_reaction(self, reaction):
        content = {
            "m.relates_to": {
                "rel_type": "m.annotation",
                "event_id": reaction.linked_event.event_id,
                "key": reaction.emoji,
            }
        }
        return await self.connection.room_send(
            reaction.target,
            "m.reaction",
            content,
            ignore_unverified_devices=self._ignore_unverified,
        )

    async def _get_file_info(self, file_event):
        info_dict = {}
        if isinstance(file_event, events.Image):
            info_dict["w"], info_dict["h"] = await file_event.get_dimensions()

        info_dict["mimetype"] = await file_event.get_mimetype()
        info_dict["size"] = len(await file_event.get_file_bytes())

        return info_dict

    async def _file_to_mxc_url(self, file_event):
        """Given a file event return the mxc url."""
        uploaded = False
        mxc_url = None
        file_dict = None
        if file_event.url:
            url = urlparse(file_event.url)
            if url.scheme == "mxc":
                mxc_url = file_event.url

        if not mxc_url:
            encrypt_file = (
                self._allow_encryption
                and file_event.target in self.connection.store.load_encrypted_rooms()
            )
            upload_file = await file_event.get_file_bytes()
            mimetype = await file_event.get_mimetype()

            response = await self.connection.upload(
                lambda x, y: upload_file, content_type=mimetype, encrypt=encrypt_file
            )

            response, file_dict = response

            if isinstance(response, nio.UploadError):
                _LOGGER.error(
                    f"Error while sending the file. Reason: {response.message} (status code {response.status_code})"
                )
                return response, None, None

            mxc_url = response.content_uri
            uploaded = True

            if file_dict:
                file_dict["url"] = mxc_url
                file_dict["mimetype"] = mimetype

        return mxc_url, uploaded, file_dict

    @register_event(events.File)
    @register_event(events.Image)
    @ensure_room_id_and_send
    async def _send_file(self, file_event):
        mxc_url, uploaded, file_dict = await self._file_to_mxc_url(file_event)

        if isinstance(mxc_url, nio.UploadError):
            return

        name = file_event.name or "opsdroid_upload"
        if uploaded:
            extra_info = await self._get_file_info(file_event)
        else:
            extra_info = {}
        msg_type = f"m.{file_event.__class__.__name__}".lower()

        content = {
            "body": name,
            "info": extra_info,
            "msgtype": msg_type,
            "url": mxc_url,
        }

        if file_dict:
            content["file"] = file_dict
            del content["url"]

        await self.connection.room_send(
            room_id=file_event.target,
            message_type="m.room.message",
            content=content,
            ignore_unverified_devices=self._ignore_unverified,
        )

    @register_event(events.NewRoom)
    @ensure_room_id_and_send
    async def _send_room_creation(self, creation_event):
        params = creation_event.room_params
        params = params.get("matrix", params)
        response = await self.connection.room_create(**params)
        if isinstance(response, nio.RoomCreateError):
            _LOGGER.error(
                f"Error while creating the room. Reason: {response.message} (status code {response.status_code})"
            )
            return
        room_id = response.room_id
        if creation_event.name is not None:
            await self._send_room_name_set(
                events.RoomName(creation_event.name, target=room_id)
            )
        return room_id

    @register_event(events.RoomName)
    @ensure_room_id_and_send
    async def _send_room_name_set(self, name_event):
        return await self.connection.room_put_state(
            name_event.target, "m.room.name", {"name": name_event.name}
        )

    @register_event(events.RoomAddress)
    @ensure_room_id_and_send
    async def _send_room_address(self, address_event):
        res = await self.connection.room_put_state(
            address_event.target, "m.room.aliases", address_event.address
        )

        if isinstance(res, nio.RoomPutStateError) and res.status_code == 409:
            _LOGGER.warning(
                f"A room with the alias {address_event.address} already exists."
            )
            return

        return res

    @register_event(events.JoinRoom)
    @ensure_room_id_and_send
    async def _send_join_room(self, join_event):
        return await self.connection.join(join_event.target)

    @register_event(events.UserInvite)
    @ensure_room_id_and_send
    async def _send_user_invitation(self, invite_event):
        res = await self.connection.room_invite(
            invite_event.target, invite_event.user_id
        )

        if isinstance(res, nio.RoomInviteError):
            if res.status_code == 403 and "is already in the room" in res.message:
                _LOGGER.info(
                    f"{invite_event.user_id} is already in the room, ignoring."
                )
                return

        return res

    @register_event(events.RoomDescription)
    @ensure_room_id_and_send
    async def _send_room_desciption(self, desc_event):
        return await self.connection.room_put_state(
            desc_event.target, "m.room.topic", {"topic": desc_event.description}
        )

    @register_event(events.RoomImage)
    @ensure_room_id_and_send
    async def _send_room_image(self, image_event):
        mxc_url, _, _ = await self._file_to_mxc_url(image_event.room_image)
        return await image_event.respond(matrixevents.MatrixRoomAvatar(mxc_url))

    @register_event(events.UserRole)
    @ensure_room_id_and_send
    async def _set_user_role(self, role_event):
        if not role_event.user_id:
            raise ValueError("Can't send a UserRole without the user_id attribute set.")

        role = role_event.role
        room_id = role_event.target
        if isinstance(role, str) and role.lower() in ["mod", "moderator"]:
            power_level = 50
        elif isinstance(role, str) and role.lower() in ["admin", "administrator"]:
            power_level = 100
        else:
            try:
                power_level = int(role)
            except ValueError:
                raise ValueError("Role must be one of 'mod', 'admin', or an integer")

        power_levels = await self.connection.room_get_state_event(
            room_id, "m.room.power_levels"
        )
        power_levels.content["users"][role_event.user_id] = power_level

        return await role_event.respond(matrixevents.MatrixPowerLevels(power_levels))

    @register_event(matrixevents.MatrixStateEvent, include_subclasses=True)
    @ensure_room_id_and_send
    async def _send_state_event(self, state_event):
        _LOGGER.debug(f"Sending State Event {state_event}")
        return await self.connection.room_put_state(
            state_event.target,
            state_event.event_type,
            state_event.content,
            state_key=state_event.state_key,
        )

    @register_event(matrixevents.GenericMatrixRoomEvent)
    @ensure_room_id_and_send
    async def _send_generic_event(self, event):
        return await self.connection.room_send(
            event.target,
            event.event_type,
            event.content,
            ignore_unverified_devices=self._ignore_unverified,
        )
