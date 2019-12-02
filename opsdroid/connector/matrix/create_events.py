"""A helper module to create opsdroid events from matrix events."""
from collections import defaultdict
from opsdroid import events


__all__ = ["MatrixEventCreator"]


class MatrixEventCreator(events.EventCreator):
    """Create opsdroid events from matrix ones."""

    def __init__(self, connector, *args, **kwargs):
        """Initialise the event creator."""
        super().__init__(connector, *args, **kwargs)

        self.event_types["m.room.message"] = self.create_room_message
        self.event_types["m.room.topic"] = self.create_room_description
        self.event_types["m.room.name"] = self.create_room_name
        self.event_types["m.reaction"] = self.create_reaction

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
        # Detect an edit.
        if (
            "m.relates_to" in event["content"]
            and event["content"]["m.relates_to"]["rel_type"] == "m.replace"
        ):
            kwargs["text"] = event["content"]["m.new_content"]["body"]
            kwargs["edited_event"] = event["content"]["m.relates_to"]["event_id"]
            return events.EditedMessage(**kwargs)
        else:
            return events.Message(**kwargs)

    async def _file_kwargs(self, event, roomid):
        url = self.connector.connection.get_download_url(event["content"]["url"])
        return dict(
            url=url,
            name=event["content"]["body"],
            user_id=event["sender"],
            user=await self.connector.get_nick(roomid, event["sender"]),
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
        return events.Reaction(
            emoji=event["content"]["m.relates_to"]["key"],
            user=await self.connector.get_nick(roomid, event["sender"]),
            user_id=event["sender"],
            target=roomid,
            connector=self.connector,
            event_id=event["event_id"],
            # TODO: Lookup this event and return the proper event class for it.
            linked_event=event["content"]["m.relates_to"]["event_id"],
            raw_event=event,
        )
