"""Connector for Matrix (https://matrix.org)."""

import re
import json
import logging
import functools
from concurrent.futures import CancelledError
from urllib.parse import urlparse

import aiohttp

from matrix_api_async.api_asyncio import AsyncHTTPAPI
from matrix_client.errors import MatrixRequestError
from voluptuous import Required

from opsdroid.connector import Connector, register_event
from opsdroid import events

from .html_cleaner import clean
from .create_events import MatrixEventCreator
from . import events as matrixevents


_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = {
    Required("mxid"): str,
    Required("password"): str,
    Required("rooms"): dict,
    "homeserver": str,
    "nick": str,
    "room_specific_nicks": bool,
}

__all__ = ["ConnectorMatrix"]


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
            event.target = await self.connection.get_room_id(event.target)

        try:
            return await func(self, event)
        except aiohttp.client_exceptions.ServerDisconnectedError:
            _LOGGER.debug(_("Server had disconnected, retrying send."))
            return await func(self, event)

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
        self.nick = config.get("nick", None)
        self.homeserver = config.get("homeserver", "https://matrix.org")
        self.password = config["password"]
        self.room_specific_nicks = config.get("room_specific_nicks", False)
        self.send_m_notice = config.get("send_m_notice", False)
        self.session = None
        self.filter_id = None
        self.connection = None

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

    async def make_filter(self, api):
        """Make a filter on the server for future syncs."""
        fjson = self.filter_json
        resp = await api.create_filter(user_id=self.mxid, filter_params=fjson)
        return resp["filter_id"]

    async def connect(self):
        """Create connection object with chat library."""
        session = aiohttp.ClientSession(trust_env=True)
        mapi = AsyncHTTPAPI(self.homeserver, session)

        self.session = session
        login_response = await mapi.login(
            "m.login.password", user=self.mxid, password=self.password
        )
        mapi.token = login_response["access_token"]
        mapi.sync_token = None

        for roomname, room in self.rooms.items():
            response = await mapi.join_room(room["alias"])
            self.room_ids[roomname] = response["room_id"]
        self.connection = mapi

        # Create a filter now, saves time on each later sync
        self.filter_id = await self.make_filter(mapi)

        # Do initial sync so we don't get old messages later.
        response = await self.connection.sync(
            timeout_ms=3000,
            filter='{ "room": { "timeline" : { "limit" : 1 } } }',
            set_presence="online",
        )
        self.connection.sync_token = response["next_batch"]

        if self.nick:
            display_name = await self.connection.get_display_name(self.mxid)
            if display_name != self.nick:
                await self.connection.set_display_name(self.mxid, self.nick)

    async def disconnect(self):
        """Close the matrix session."""
        await self.session.close()

    async def _parse_sync_response(self, response):
        self.connection.sync_token = response["next_batch"]

        # Emit Invite events for every room in the invite list.
        for roomid, room in response["rooms"]["invite"].items():
            # Process the invite list to extract the person who invited us.
            invite_event = [
                e
                for e in room["invite_state"]["events"]
                if "invite" == e.get("content", {}).get("membership")
            ][0]
            sender = await self.get_nick(None, invite_event["sender"])

            await self.opsdroid.parse(
                events.UserInvite(
                    target=roomid,
                    user_id=invite_event["sender"],
                    user=sender,
                    connector=self,
                    raw_event=invite_event,
                )
            )

        for roomid, room in response["rooms"]["join"].items():
            if "timeline" in room:
                for event in room["timeline"]["events"]:
                    if event["sender"] != self.mxid:
                        return await self._event_creator.create_event(event, roomid)

    async def listen(self):  # pragma: no cover
        """Listen for new messages from the chat service."""
        while True:  # pylint: disable=R1702
            try:
                response = await self.connection.sync(
                    self.connection.sync_token,
                    timeout_ms=int(60 * 1e3),  # 1m in ms
                    filter=self.filter_id,
                )
                _LOGGER.debug(_("Matrix sync request returned."))
                message = await self._parse_sync_response(response)
                if message:
                    await self.opsdroid.parse(message)

            except MatrixRequestError as mre:
                # We can safely ignore timeout errors. The non-standard error
                # codes are returned by Cloudflare.
                if mre.code in [504, 522, 524]:
                    _LOGGER.info(_("Matrix sync timeout (code: %d)."), mre.code)
                    continue

                _LOGGER.exception(_("Matrix sync error."))
            except CancelledError:
                raise
            except Exception:  # pylint: disable=W0703
                _LOGGER.exception(_("Matrix sync error."))

    async def get_nick(self, roomid, mxid):
        """
        Get nickname from user ID.

        Get the nickname of a sender depending on the room specific config
        setting.
        """
        if self.room_specific_nicks:
            try:
                return await self.connection.get_room_displayname(roomid, mxid)
            except Exception:  # pylint: disable=W0703
                # Fallback to the non-room specific one
                logging.exception("Failed to lookup room specific nick for %s.", mxid)

        try:
            return await self.connection.get_display_name(mxid)
        except MatrixRequestError as mre:
            # Log the error if it's not the 404 from the user not having a nick
            if mre.code != 404:
                logging.exception("Failed to lookup nick for %s.", mxid)
            return mxid

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
        return await self.connection.send_message_event(
            message.target,
            "m.room.message",
            self._get_formatted_message_body(
                message.text, msgtype=self.message_type(message.target)
            ),
        )

    @register_event(events.EditedMessage)
    @ensure_room_id_and_send
    async def _send_edit(self, message):
        if isinstance(message.linked_event, events.EditedMessage):
            # If we are attempting to edit an edit, move up the tree and then
            # try again.
            message.linked_event = message.linked_event.linked_event
            return self._send_edit(message)
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

        return (
            await self.connection.send_message_event(
                message.target, "m.room.message", content
            ),
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

        return (
            await self.connection.send_message_event(
                reply.target, "m.room.message", content
            ),
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
        return await self.connection.send_message_event(
            reaction.target, "m.reaction", content
        )

    async def _get_image_info(self, image):
        width, height = await image.get_dimensions()
        return {
            "w": width,
            "h": height,
            "mimetype": await image.get_mimetype(),
            "size": len(await image.get_file_bytes()),
        }

    async def _file_to_mxc_url(self, file_event):
        """Given a file event return the mxc url."""
        uploaded = False
        mxc_url = None
        if file_event.url:
            url = urlparse(file_event.url)
            if url.scheme == "mxc":
                mxc_url = file_event.url

        if not mxc_url:
            mxc_url = await self.connection.media_upload(
                await file_event.get_file_bytes(), await file_event.get_mimetype()
            )

            mxc_url = mxc_url["content_uri"]
            uploaded = True

        return mxc_url, uploaded

    @register_event(events.File)
    @register_event(events.Image)
    @ensure_room_id_and_send
    async def _send_file(self, file_event):
        mxc_url, uploaded = await self._file_to_mxc_url(file_event)

        if isinstance(file_event, events.Image):
            if uploaded:
                extra_info = await self._get_image_info(file_event)
            else:
                extra_info = {}
            msg_type = "m.image"
        else:
            extra_info = {}
            msg_type = "m.file"

        name = file_event.name or "opsdroid_upload"
        await self.connection.send_content(
            file_event.target, mxc_url, name, msg_type, extra_info
        )

    @register_event(events.NewRoom)
    @ensure_room_id_and_send
    async def _send_room_creation(self, creation_event):
        params = creation_event.room_params
        params = params.get("matrix", params)
        response = await self.connection.create_room(**params)
        room_id = response["room_id"]
        if creation_event.name is not None:
            await self._send_room_name_set(
                events.RoomName(creation_event.name, target=room_id)
            )
        return room_id

    @register_event(events.RoomName)
    @ensure_room_id_and_send
    async def _send_room_name_set(self, name_event):
        return await self.connection.set_room_name(name_event.target, name_event.name)

    @register_event(events.RoomAddress)
    @ensure_room_id_and_send
    async def _send_room_address(self, address_event):
        try:
            return await self.connection.set_room_alias(
                address_event.target, address_event.address
            )
        except MatrixRequestError as err:
            if err.code == 409:
                _LOGGER.warning(
                    f"A room with the alias {address_event.address} already exists."
                )

    @register_event(events.JoinRoom)
    @ensure_room_id_and_send
    async def _send_join_room(self, join_event):
        return await self.connection.join_room(join_event.target)

    @register_event(events.UserInvite)
    @ensure_room_id_and_send
    async def _send_user_invitation(self, invite_event):
        try:
            return await self.connection.invite_user(
                invite_event.target, invite_event.user_id
            )
        except MatrixRequestError as err:
            content = json.loads(err.content)
            if err.code == 403 and "is already in the room" in content["error"]:
                _LOGGER.info(
                    f"{invite_event.user_id} is already in the room, ignoring."
                )

    @register_event(events.RoomDescription)
    @ensure_room_id_and_send
    async def _send_room_desciption(self, desc_event):
        return await self.connection.set_room_topic(
            desc_event.target, desc_event.description
        )

    @register_event(events.RoomImage)
    @ensure_room_id_and_send
    async def _send_room_image(self, image_event):
        mxc_url, _ = await self._file_to_mxc_url(image_event.room_image)
        return await image_event.respond(matrixevents.MatrixRoomAvatar(mxc_url))

    @register_event(events.UserRole)
    @ensure_room_id_and_send
    async def _set_user_role(self, role_event):
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

        power_levels = await self.connection.get_power_levels(room_id)
        power_levels["users"][role_event.user_id] = power_level

        return await role_event.respond(matrixevents.MatrixPowerLevels(power_levels))

    @register_event(matrixevents.MatrixStateEvent, include_subclasses=True)
    @ensure_room_id_and_send
    async def _send_state_event(self, state_event):
        _LOGGER.debug(f"Sending State Event {state_event}")
        return await self.connection.send_state_event(
            state_event.target,
            state_event.key,
            state_event.content,
            state_key=state_event.state_key,
        )
