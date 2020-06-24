"""A helper module to create opsdroid events from matrix events."""
import logging
from collections import defaultdict

from opsdroid import events

from . import events as matrix_events

_LOGGER = logging.getLogger(__name__)

__all__ = ["MatrixEventCreator"]


def trim_reply_fallback_text(text):
    # Copyright (C) 2018 Tulir Asokan
    # Borrowed from https://github.com/tulir/mautrix-telegram
    # Having been given explicit permission to include it "under the terms of any OSI approved licence"
    # https://matrix.to/#/!FPUfgzXYWTKgIrwKxW:matrix.org/$15365871364925maRqg:maunium.net

    if not text.startswith("> ") or "\n" not in text:
        return text  # pragma: no cover
    lines = text.split("\n")
    while len(lines) > 0 and lines[0].startswith("> "):
        lines.pop(0)
    return "\n".join(lines).strip()


class MatrixEventCreator(events.EventCreator):
    """Create opsdroid events from matrix ones."""

    async def create_event_from_eventid(self, eventid, roomid):
        """Return an ``Event`` based on an event id in a room."""
        room_context = await self.connector.connection.room_context(roomid, eventid, 1)
        event_json = room_context.event.source
        return await self.create_event(event_json, roomid)

    def __init__(self, connector, *args, **kwargs):
        """Initialise the event creator."""
        super().__init__(connector, *args, **kwargs)

        self.event_types["m.room.message"] = self.create_room_message
        self.event_types["m.room.topic"] = self.create_room_description
        self.event_types["m.room.name"] = self.create_room_name
        self.event_types["m.reaction"] = self.create_reaction
        self.event_types["m.room.member"] = self.create_join_room

        self.message_events = defaultdict(lambda: self.skip)
        self.message_events.update(
            {
                "m.text": self.create_message,
                "m.image": self.create_image,
                "m.file": self.create_file,
                # 'm.emote':
                # 'm.notice':
                # 'm.video':
                # 'm.audio':
                # 'm.location':
            }
        )

    async def skip(self, event, roomid):
        """Generate a generic event (state event if appropriate)."""
        kwargs = dict(
            content=event["content"],
            event_type=event["type"],
            user_id=event["sender"],
            user=await self.connector.get_nick(roomid, event["sender"]),
            target=roomid,
            connector=self.connector,
            raw_event=event,
            event_id=event["event_id"],
        )
        event_type = matrix_events.GenericMatrixRoomEvent
        if "state_key" in event:
            event_type = matrix_events.MatrixStateEvent
            kwargs["state_key"] = event["state_key"]
        try:
            event = event_type(**kwargs)
            return event
        except Exception:  # pragma: nocover
            _LOGGER.exception(
                f"Matrix connector failed to parse event {event} as a room event."
            )
            return None

    async def create_room_message(self, event, roomid):
        """Dispatch a m.room.message event."""
        msgtype = event["content"]["msgtype"]
        return await self.message_events[msgtype](event, roomid)

    async def create_message(self, event, roomid):
        """Send a Message event."""
        kwargs = dict(
            text=event["content"]["body"],
            user_id=event["sender"],
            user=await self.connector.get_nick(roomid, event["sender"]),
            target=roomid,
            connector=self.connector,
            event_id=event["event_id"],
            raw_event=event,
        )
        if "m.relates_to" in event["content"]:
            relates_to = event["content"]["m.relates_to"]
            # Detect an edit.
            if relates_to.get("rel_type", "") == "m.replace":
                kwargs["text"] = event["content"]["m.new_content"]["body"]
                kwargs["linked_event"] = await self.create_event_from_eventid(
                    relates_to["event_id"], roomid
                )
                return events.EditedMessage(**kwargs)
            # Detect a reply
            if relates_to.get("m.in_reply_to"):
                kwargs["text"] = trim_reply_fallback_text(kwargs["text"])
                kwargs["linked_event"] = await self.create_event_from_eventid(
                    relates_to["m.in_reply_to"]["event_id"], roomid
                )
                return events.Reply(**kwargs)

        return events.Message(**kwargs)

    async def _file_kwargs(self, event, roomid):

        if "url" in event["content"]:
            url = event["content"]["url"]
        else:
            url = event["content"]["file"]["url"]

        url = await self.connector.connection.mxc_to_http(url)
        user = await self.connector.get_nick(roomid, event["sender"])

        return dict(
            url=url,
            name=event["content"]["body"],
            user_id=event["sender"],
            user=user,
            target=roomid,
            connector=self.connector,
            event_id=event["event_id"],
            raw_event=event,
        )

    async def create_file(self, event, roomid):
        """Send a File event."""
        kwargs = await self._file_kwargs(event, roomid)
        return events.File(**kwargs)

    async def create_image(self, event, roomid):
        """Send a Image event."""
        kwargs = await self._file_kwargs(event, roomid)
        return events.Image(**kwargs)

    async def create_room_description(self, event, roomid):
        """Send a RoomDescriptionEvent."""
        return events.RoomDescription(
            description=event["content"]["topic"],
            user=await self.connector.get_nick(roomid, event["sender"]),
            user_id=event["sender"],
            target=roomid,
            connector=self.connector,
            event_id=event["event_id"],
            raw_event=event,
        )

    async def create_room_name(self, event, roomid):
        """Send a RoomDescriptionEvent."""
        return events.RoomName(
            name=event["content"]["name"],
            user=await self.connector.get_nick(roomid, event["sender"]),
            user_id=event["sender"],
            target=roomid,
            connector=self.connector,
            event_id=event["event_id"],
            raw_event=event,
        )

    async def create_reaction(self, event, roomid):
        """Send a Reaction event."""
        parent_event_id = event["content"]["m.relates_to"]["event_id"]
        parent_event = await self.create_event_from_eventid(parent_event_id, roomid)
        return events.Reaction(
            emoji=event["content"]["m.relates_to"]["key"],
            user=await self.connector.get_nick(roomid, event["sender"]),
            user_id=event["sender"],
            target=roomid,
            connector=self.connector,
            event_id=event["event_id"],
            linked_event=parent_event,
            raw_event=event,
        )

    async def create_join_room(self, event, roomid):
        """Send a JoinRoomEvent."""
        if event["content"]["membership"] == "join":
            return events.JoinRoom(
                user=await self.connector.get_nick(roomid, event["sender"]),
                user_id=event["sender"],
                target=roomid,
                connector=self.connector,
                event_id=event["event_id"],
                raw_event=event,
            )
