"""A helper module to create opsdroid events from matrix events."""
from collections import defaultdict
from opsdroid import events


__all__ = ['MatrixEventCreator']


class MatrixEventCreator:
    """Create opsdroid events from matrix ones."""

    def __init__(self, connector):
        """Initialise the event creator."""
        self.connector = connector

        self.event_types = defaultdict(lambda: self.skip)
        self.event_types['m.room.message'] = self.create_room_message

        self.message_events = defaultdict(lambda: self.skip)
        self.message_events.update({
            'm.text': self.create_message,
            'm.image': self.create_image,
            'm.file': self.create_file,
            # 'm.emote':
            # 'm.notice':
            # 'm.video':
            # 'm.audio':
            # 'm.location':
        })

    async def create_event(self, event, roomid):
        """Dispatch any matrix event."""
        return await self.event_types[event['type']](event, roomid)

    async def create_room_message(self, event, roomid):
        """Dispatch a m.room.message event."""
        msgtype = event['content']['msgtype']
        return await self.message_events[msgtype](event, roomid)

    @staticmethod
    async def skip(event, roomid):
        """Do not handle this event type."""
        return None

    async def create_message(self, event, roomid):
        """Send a Message event."""
        return events.Message(
            event['content']['body'],
            await self.connector.get_nick(roomid, event['sender']),
            roomid,
            self.connector,
            event_id=event['event_id'],
            raw_event=event)

    async def _file_kwargs(self, event, roomid):
        url = self.connector.connection.get_download_url(
            event['content']['url'])
        return dict(
            url=url,
            name=event['content']['body'],
            user=await self.connector.get_nick(roomid, event['sender']),
            target=roomid,
            connector=self.connector,
            event_id=event['event_id'],
            raw_event=event)

    async def create_file(self, event, roomid):
        """Send a File event."""
        kwargs = await self._file_kwargs(event, roomid)
        return events.File(**kwargs)

    async def create_image(self, event, roomid):
        """Send a Image event."""
        kwargs = await self._file_kwargs(event, roomid)
        return events.Image(**kwargs)
