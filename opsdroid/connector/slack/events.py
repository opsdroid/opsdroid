"""Classes to describe different kinds of Slack specific event."""

import json

from opsdroid import events


class Blocks(events.Message):
    """A blocks object.

    Slack uses blocks to add advenced interactivity and formatting to messages.
    https://api.slack.com/messaging/interactivity
    Blocks are provided in JSON format to Slack which renders them.

    Args:
        blocks (string or dict): String or dict of json for blocks
        room (string, optional): String name of the room or chat channel in
                                 which message was sent
        connector (Connector, optional): Connector object used to interact with
                                         given chat service
        raw_event (dict, optional): Raw message as provided by chat service.
                                    None by default

    Attributes:
        created: Local date and time that message object was created
        user: String name of user sending message
        room: String name of the room or chat channel in which message was sent
        connector: Connector object used to interact with given chat service
        blocks: Blocks JSON as string
        raw_event: Raw message provided by chat service
        raw_match: A match object for a search against which the message was
            matched. E.g. a regular expression or natural language intent
        responded_to: Boolean initialized as False. True if event has been
            responded to

    """

    def __init__(self, blocks, *args, **kwargs):
        """Create object with minimum properties."""
        super().__init__("", *args, **kwargs)

        self.blocks = blocks
        if isinstance(self.blocks, list):
            self.blocks = json.dumps(self.blocks)


class SlackEventCreator:
    """Create opsdroid events from Slack ones."""

    def __init__(self, connector):
        """Initialise the event creator"""
        self.connector = connector

        self.event_types = defaultdict(lambda: self.skip)
        self.event_types['message'] = self.create_room_message

        self.message_events = defaultdict(lambda: self.skip)
        self.message_events.update(
            {
                "message": self.create_message,
            }
        )

    async def create_event(self, event, channel):
        """Dispatch any Slack event."""
        return await self.event_types[event["type"]](event, channel)

    async def create_room_message(self, event, channel):
        """Dispatch a message event of arbitrary subtype."""
        msgtype = event['subtype'] if 'subtype' in event.keys() else 'message'
        return await self.message_events[msgtype](event, channel)

    @staticmethod
    async def skip(event, roomid):
        """Do not handle this event type"""
        return None

    async def create_message(self, event, channel):
        """Send a Message event."""
        return events.Message(
            event['text'],
            event['user'],
            channel,
            self.connector,
            event_id=event["ts"],
            raw_event=event
        )
