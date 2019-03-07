"""Classes to describe different kinds of possible event."""

import asyncio
from abc import ABC
from random import randrange
from datetime import datetime

import aiohttp

from opsdroid.helper import get_opsdroid


# pylint: disable=too-few-public-methods,keyword-arg-before-vararg
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
        event_id (object, optional): The unique id for this event as provided
                                     by the connector.
        linked_event (Event, optional): An event to link to this one, i.e. the
                                        event that a reaction applies to.

    Attributes:
        created: Local date and time that message object was created
        user: String name of user sending message
        target: String name of the room or chat channel in which message
                was sent.
        connector: Connector object used to interact with given chat service
        raw_event: Raw event provided by chat service
        responded_to: Boolean initialized as False. True if event has been
            responded to

    """

    def __init__(self, user=None, target=None, connector=None, raw_event=None,
                 event_id=None, linked_event=None):  # noqa: D107
        self.user = user
        self.target = target
        self.connector = connector
        self.linked_event = linked_event

        self.created = datetime.now()
        self.event_id = event_id
        self.raw_event = raw_event
        self.responded_to = False

    async def respond(self, event):
        """Respond to this event with another event.

        This implies no link between the event we are responding with and this
        event.
        """
        opsdroid = get_opsdroid()

        # Inherit the user, target and event from the event we are responding
        # to if they are not explicitly provided by this Event
        event.user = event.user or self.user
        event.target = event.target or self.target
        event.connector = event.connector or self.connector
        event.linked_event = event.linked_event or self

        await opsdroid.send(event)

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

    def __init__(self, text, *args, **kwargs):
        """Create object with minimum properties."""
        super().__init__(*args, **kwargs)
        self.text = text
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

        # TODO: Add support for sending typing events here
        await asyncio.sleep(char_count*seconds)

    async def respond(self, event):
        """Respond to this message using the connector it was created by.

        Creates copy of this message with updated text as response.
        Delays message if thinking or typing delay present in config. file.
        Updates responded_to attribute to True if False.
        Logs response and response time in OpsDroid object stats.
        """
        if isinstance(event, str):
            response = Message(event)
        else:
            response = event

        if 'thinking-delay' in self.connector.configuration or \
           'typing-delay' in self.connector.configuration:
            await self._thinking_delay()
            if isinstance(response, Message):
                await self._typing_delay(response.text)

        await super().respond(response)


class Typing(Event):  # pragma: nocover
    """An event to set the user typing.

    Args:
        trigger (bool): Trigger typing on or off.
        timeout (float, optional): Timeout on typing event.

    """

    def __init__(self, trigger, timeout=None, *args, **kwargs):
        """Create the object."""
        self.timeout = timeout
        self.trigger = trigger
        super().__init__(self, *args, **kwargs)


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

    def __init__(self, emoji, *args, **kwargs):  # noqa: D107
        super().__init__(*args, **kwargs)
        self.emoji = emoji


class File(Event):
    """Event class to represent arbitrary files as bytes."""

    def __init__(self, file_bytes=None, url=None,
                 *args, **kwargs):  # noqa: D107
        if not (file_bytes or url) or (file_bytes and url):
            raise ValueError("Either file_bytes or url must be specified")

        super().__init__(*args, **kwargs)

        self._file_bytes = file_bytes
        self.url = url

    async def get_file_bytes(self):  # noqa: D401
        """Return the bytes representation of this file."""
        if not self._file_bytes and self.url:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url) as resp:
                    self._file_bytes = await resp.read()

        return self._file_bytes


class Image(File):
    """Event class specifically for image files."""
