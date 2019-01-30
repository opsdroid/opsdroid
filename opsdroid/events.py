"""Classes to describe different kinds of possible event."""

import asyncio
from abc import ABC
from copy import copy
from random import randrange
from datetime import datetime

from opsdroid.helper import get_opsdroid


# pylint: disable=too-few-public-methods
class Event(ABC):
    """A generic event type.

    Initiates an Event object with the most basic information about its
    creation.

    Args:
        user (string, optional): String name of user sending message
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
        raw_event: Raw event provided by chat service
        responded_to: Boolean initialized as False. True if event has been
            responded to

    """

    def __init__(self, user=None, target=None,
                 connector=None, raw_event=None):  # noqa: D107
        self.created = datetime.now()
        self.user = user
        self.target = target
        self.connector = connector
        self.raw_event = raw_event
        self.responded_to = False

    def respond(self, event, target=None):
        opsdroid = get_opsdroid()
        event.prev_event = self
        # Inherit the user, target and event from the event we are responding
        # to if they are not explicitly provided by this Event
        event.user = event.user if event.user else self.user
        event.target = event.target if event.target else self.target
        event.connector = event.connector if event.connector else self.connector

        await self.connector.send(event, target)

        if not self.responded_to:
            now = datetime.now()
            opsdroid.stats["total_responses"] = \
                opsdroid.stats["total_responses"] + 1
            opsdroid.stats["total_response_time"] = \
                opsdroid.stats["total_response_time"] + \
                (now - self.created).total_seconds()
            self.responded_to = True


class Message(Event):
    """A message object.

    Stores messages in a format that allows OpsDroid to respond or react with
    delays for thinking and typing as defined in configuration YAML file.

    Args:
        text (string): String text of message
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
        text: Text of message as string
        raw_event: Raw message provided by chat service
        raw_match: A match object for a search against which the message was
            matched. E.g. a regular expression or natural language intent
        responded_to: Boolean initialized as False. True if event has been
            responded to

    """

    def __init__(self, text, **kwargs):
        """Create object with minimum properties."""
        super().__init__(**kwargs)
        self.text = text
        self.raw_message = self.raw_event  # For backwards compatibility
        self.raw_match = None

    async def _thinking_delay(self):
        """Make opsdroid wait x-seconds before responding.

        Number of seconds defined in YAML config. file, accessed via connector.
        """
        seconds = self.connector.configuration.get('thinking-delay', 0)

        if isinstance(seconds, list):
            seconds = randrange(seconds[0], seconds[1])

        await asyncio.sleep(seconds)

    async def _typing_delay(self, text):
        """Delays reply to simulate typing.

        Seconds to delay equals number of characters in response multiplied by
        number of seconds defined in YAML config. file, accessed via connector.
        """
        seconds = self.connector.configuration.get('typing-delay', 0)
        char_count = len(text)

        if isinstance(seconds, list):
            seconds = randrange(seconds[0], seconds[1])

        await asyncio.sleep(char_count*seconds)

    async def respond(self, response_event, target=None):
        """Respond to this message using the connector it was created by.

        Creates copy of this message with updated text as response.
        Delays message if thinking or typing delay present in config. file.
        Updates responded_to attribute to True if False.
        Logs response and response time in OpsDroid object stats.
        """
        if isinstance(response_event, str):
            response = copy(self)
            response.text = response_event
        else:
            response = response_event

        response.prev_event = self

        if 'thinking-delay' in self.connector.configuration or \
           'typing-delay' in self.connector.configuration:
            await self._thinking_delay()
            await self._typing_delay(response.text)

        await super().respond(response, target)


class Reaction(Event):
    """Event class to support Unicode reaction to an event.

    Args:
        emoji (string): The emoji to react with.
        room (string, optional): String name of the room or chat channel in
                                 which message was sent
        connector (Connector, optional): Connector object used to interact with
                                         given chat service
        raw_event (dict, optional): Raw message as provided by chat service.
                                    None by default
    """
    def __init__(self, emoji, **kwargs):
        super().__init__(**kwargs)
        self.emoji = emoji


class File(Event):
    """Event class to represent arbitrary files as bytes."""

    def __init__(self, file_bytes=None, url=None, **kwargs):  # noqa: D107
        if not file_bytes or url:
            raise ValueError("Either file_bytes or url must be specified")

        super().__init__(**kwargs)

        self.file_bytes = file_bytes
        self.url = url


class Image(File):
    """Event class specifically for image files."""

    def __init__(self, image_bytes=None, image_url=None, **kwargs):  # noqa: D107
        super().__init__(file_bytes=image_bytes, url=image_url, **kwargs)
