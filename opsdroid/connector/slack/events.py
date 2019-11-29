"""Classes to describe different kinds of Slack specific event."""

import json

from opsdroid.events import Message, Event


class Blocks(Message):
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


class BlockActions(Event):
    """Event class to represent block_actions in Slack."""

    def __init__(self, payload, *args, **kwargs):
        """Create object with minimum properties."""
        super().__init__(*args, **kwargs)

        self.payload = payload
        if isinstance(self.payload, list):
            self.payload = json.dumps(self.payload)


class MessageActions(Event):
    """Event class to represent message_actions in Slack."""

    def __init__(self, payload, *args, **kwargs):
        """Create object with minimum properties."""
        super().__init__(*args, **kwargs)

        self.payload = payload
        if isinstance(self.payload, list):
            self.payload = json.dumps(self.payload)


class ViewSubmission(Event):
    """Event class to represent view_submission in Slack."""

    def __init__(self, payload, *args, **kwargs):
        """Create object with minimum properties."""
        super().__init__(*args, **kwargs)

        self.payload = payload
        if isinstance(self.payload, list):
            self.payload = json.dumps(self.payload)


class ViewClosed(Event):
    """Event class to represent view_closed in Slack."""

    def __init__(self, payload, *args, **kwargs):
        """Create object with minimum properties."""
        super().__init__(*args, **kwargs)

        self.payload = payload
        if isinstance(self.payload, list):
            self.payload = json.dumps(self.payload)
