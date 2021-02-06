"""Classes to describe different kinds of possible event."""
import asyncio
import io
import logging
import tempfile
from abc import ABCMeta
from collections import defaultdict
from datetime import datetime
from random import randrange
from bitstring import BitArray

import aiohttp
import puremagic
import os
from get_image_size import get_image_size_from_bytesio
from opsdroid.helper import get_opsdroid
from videoprops import get_video_properties

_LOGGER = logging.getLogger(__name__)


class EventCreator:
    """Create opsdroid events from events detected by a connector."""

    def __init__(self, connector, dispatch_key="type"):
        """Initialise the event creator."""
        self.connector = connector
        self.dispatch_key = dispatch_key

        self.event_types = defaultdict(lambda: self.skip)

    async def create_event(self, event, target):
        """Dispatch any event type."""
        return await self.event_types[event[self.dispatch_key]](event, target)

    @staticmethod
    async def skip(event, roomid):
        """Do not handle this event type."""
        return None


# pylint: disable=bad-mcs-classmethod-argument,arguments-differ
class EventMetaClass(ABCMeta):
    """Metaclass for Event.

    This metaclass keeps a mapping of event name to event class.
    """

    event_registry = {}

    def __new__(mcls, name, bases, members):  # noqa: D102
        cls = super().__new__(mcls, name, bases, members)

        # Skip registration for old message.Message class.
        if "_no_register" in members:
            return cls

        if name in mcls.event_registry and mcls.event_registry[name] is not cls:
            raise NameError(
                "An event subclass named {name} has already been "
                "defined. Event subclass names must be globally "
                "unique.".format(name=name)
            )

        mcls.event_registry[name] = cls

        return cls


# pylint: disable=too-few-public-methods,keyword-arg-before-vararg
class Event(metaclass=EventMetaClass):
    """A generic event type.

    Initiates an Event object with the most basic information about its
    creation.

    Args:
        user_id (string, optional): String id of user sending message
        user (string, optional): String name of user sending message
        target (string, optional): String name of the room or chat channel in
                                   which message was sent
        connector (Connector, optional): Connector object used to interact with
                                         given chat service
        raw_event (dict, optional): Raw message as provided by chat service.
                                    None by default
        raw_parses (dict, optional): Raw response as provided by parse service.
                                     None by default
        event_id (object, optional): The unique id for this event as provided
                                     by the connector.
        linked_event (Event, optional): An event to link to this one, i.e. the
                                        event that a reaction applies to.

    Attributes:
        connector:  A pointer to the opsdroid connector object which received the message.
        created: A timestamp of when this event was instantiated.
        entities: A dictionary mapping of entities created by parsers. These could be values extracted form sentences like locations, times, people, etc.
        event_id: A unique identifier for this event as provided by the connector.
        linked_event: Another event linked to this one, for example the event that a Message replies to.
        target: A string normally containing the name of the room or chat channel the event was sent in.
        raw_event:  The raw event received by the connector (may be None).
        raw_parses: The raw response provided by the parser service.
        responded_to: A boolean (True/False) flag indicating if this event has already had its respond method called.
        user: A string containing the username of the user who created the event.

    """

    def __init__(
        self,
        user_id=None,
        user=None,
        target=None,
        connector=None,
        raw_event=None,
        raw_parses=None,
        event_id=None,
        linked_event=None,
    ):  # noqa: D107
        self.user_id = user_id
        self.user = user
        self.target = target
        self.connector = connector
        self.linked_event = linked_event

        self.created = datetime.now()
        self.event_id = event_id
        self.raw_event = raw_event
        self.raw_parses = raw_parses or {}
        self.responded_to = False
        self.entities = {}

    async def respond(self, event):
        """Respond to this event with another event.

        This implies no link between the event we are responding with and this
        event.
        """
        opsdroid = get_opsdroid()

        # Inherit the user, target and event from the event we are responding
        # to if they are not explicitly provided by this Event
        event.user = event.user or self.user
        event.user_id = event.user_id or self.user_id or event.user
        event.target = event.target or self.target
        event.connector = event.connector or self.connector
        event.linked_event = event.linked_event or self

        result = await opsdroid.send(event)

        if not self.responded_to:
            now = datetime.now()
            opsdroid.stats["total_responses"] = opsdroid.stats["total_responses"] + 1
            opsdroid.stats["total_response_time"] = (
                opsdroid.stats["total_response_time"]
                + (now - self.created).total_seconds()
            )
            self.responded_to = True

        return result

    def update_entity(self, name, value, confidence=None):
        """Add or update an entitiy.

        Adds or updates an entitiy entry for an event.

        Args:
            name (string): Name of entity
            value (string): Value of entity
            confidence (float, optional): Confidence that entity is correct

        """
        self.entities[name] = {"value": value, "confidence": confidence}

    def get_entity(self, name):
        """Get the value of an entity by name.

        Args:
            name (string): Name of entity

        Returns:
            The value of the entity. Returns ``None`` if no such entity.

        """
        return self.entities.get(name, {}).get("value", None)


class OpsdroidStarted(Event):
    """An event to indicate that Opsdroid has loaded."""


class Message(Event):
    """A message object.

    Stores messages in a format that allows OpsDroid to respond or react with
    delays for thinking and typing as defined in configuration YAML file.

    Args:
        text (string): String text of message
        target (string, optional): String name of the room or chat channel in
                                   which message was sent
        connector (Connector, optional): Connector object used to interact with
                                         given chat service
        raw_event (dict, optional): Raw message as provided by chat service.
                                    None by default
        raw_parses (dict, optional): Raw response as provided by parse service.
                                     None by default

    Attributes:
        created: Local date and time that message object was created
        user: String name of user sending message
        target: String name of the room or chat channel in which message was sent
        connector: Connector object used to interact with given chat service
        text: Text of message as string
        raw_event: Raw message provided by chat service
        raw_parses: Raw response provided by the parser service
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

    def __repr__(self):
        """Override Message's representation so you can see the text when you print it."""
        return f"<opsdroid.events.Message(text={self.text})>"

    async def _thinking_delay(self):
        """Make opsdroid wait x-seconds before responding.

        Number of seconds defined in YAML config. file, accessed via connector.

        """
        seconds = self.connector.configuration.get("thinking-delay", 0)

        if isinstance(seconds, list):
            seconds = randrange(seconds[0], seconds[1])

        await asyncio.sleep(seconds)

    async def _typing_delay(self, text):
        """Delays reply to simulate typing.

        Seconds to delay equals number of characters in response multiplied by
        number of seconds defined in YAML config. file, accessed via connector.

        Args:
            text (str): The text input to perform typing simulation on.

        """
        seconds = self.connector.configuration.get("typing-delay", 0)
        char_count = len(text)

        if isinstance(seconds, list):
            seconds = randrange(seconds[0], seconds[1])

        # TODO: Add support for sending typing events here
        await asyncio.sleep(char_count * seconds)

    async def respond(self, response_event):
        """Respond to this message using the connector it was created by.

        Creates copy of this message with updated text as response.
        Delays message if thinking or typing delay present in config. file.
        Updates responded_to attribute to True if False.
        Logs response and response time in OpsDroid object stats.
        """
        if isinstance(response_event, str):
            response = Message(response_event)
        else:
            response = response_event

        if (
            "thinking-delay" in self.connector.configuration
            or "typing-delay" in self.connector.configuration
        ):
            await self._thinking_delay()
            if isinstance(response, Message):
                await self._typing_delay(response.text)

        return await super().respond(response)


class EditedMessage(Message):
    """A  `opsdroid.events.Message` which has been edited.

    The ``linked_event`` property should hold either an `opsdroid.events.Event`
    class or an id for an event to which the edit applies.
    The linked_event for Slack is the ts (timestamp) of the message to be edited
    """

    def __init__(self, *args, **kwargs):
        """Create object with minimum properties."""
        super().__init__(*args, **kwargs)


class Reply(Message):
    """Event class representing a message sent in reply to another Message.

    The ``linked_event`` property should hold either an `opsdroid.events.Event`
    class or an id for an event to which this message is replying.
    """


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
        target (string, optional): The room in which the reaction should be sent.
        linked_event (opsdroid.events.Event): The event to react to.

    """

    def __init__(self, emoji, *args, **kwargs):  # noqa: D107
        super().__init__(*args, **kwargs)
        self.emoji = emoji


class File(Event):
    """Event class to represent arbitrary files as bytes."""

    def __init__(
        self,
        file_bytes=None,
        url=None,
        url_headers=None,
        name=None,
        mimetype=None,
        *args,
        **kwargs,
    ):  # noqa: D107
        if not (file_bytes or url) or (file_bytes and url):
            raise ValueError("Either file_bytes or url must be specified")

        super().__init__(*args, **kwargs)

        self.name = name
        self._mimetype = mimetype
        self._file_bytes = file_bytes
        self.url = url
        self._url_headers = url_headers

    async def get_file_bytes(self):
        """Return the bytes representation of this file."""
        if not self._file_bytes and self.url:
            async with aiohttp.ClientSession(trust_env=True) as session:
                _LOGGER.debug(self._url_headers)
                async with session.get(self.url, headers=self._url_headers) as resp:
                    self._file_bytes = await resp.read()

        return self._file_bytes

    async def get_mimetype(self):
        """Return the mimetype for the file."""
        if self._mimetype:
            return self._mimetype

        try:
            results = puremagic.magic_string(await self.get_file_bytes())
        except puremagic.PureError:
            # If no results return none
            return ""

        # If for some reason we get a len 0 list
        if not results:  # pragma: nocover
            return ""

        # If we only have one result use it.
        if len(results) == 1:  # pragma: nocover
            return results[0].mime_type

        # If we have multiple matches with the same confidence, pick one that
        # actually has a mime_type.
        confidence = results[0].confidence
        results = filter(lambda x: x.confidence == confidence, results)
        results = list(filter(lambda x: bool(x.mime_type), results))
        return results[0].mime_type


class Image(File):
    """Event class specifically for image files."""

    async def get_dimensions(self):
        """Return the image dimensions `(w,h)`."""
        fbytes = await self.get_file_bytes()
        return get_image_size_from_bytesio(io.BytesIO(fbytes), len(fbytes))


class Video(File):
    """Event class specifically for video files."""

    async def get_bin(self):
        """Return the binary representation of video."""

        """
        The two below lines gets a bitarray of the video bytes.This method enable video bytes to be converted to hex/bin.
        Doc: https://github.com/scott-griffiths/bitstring/blob/master/doc/bitarray.rst
        """
        fbytes = await self.get_file_bytes()
        my_bit_array = BitArray(fbytes)

        # Return that bitarray
        return my_bit_array.bin

    async def get_properties(self):
        """Get the video properties like codec, resolution.Returns Video properties saved in a Dictionary."""

        """
        NamedTemporaryFile is too hard to use portably when you need to open the file by name after writing it.
        On posix you can open the file for reading by name without closing it first.
        But on Windows, To do that you need to close the file first, which means you have to pass delete=False,
        which in turn means that you get no help in cleaning up the actual file resource.
        """

        fbytes = await self.get_file_bytes()  # get bytes of file

        temp_vid = tempfile.NamedTemporaryFile(
            prefix="opsdroid_vid_", delete=False
        )  # create a file to store the bytes
        temp_vid.write(fbytes)
        temp_vid.close()

        try:
            vid_details = get_video_properties(temp_vid.name)
            os.remove(temp_vid.name)  # delete the temp file
            return vid_details
        except RuntimeError as error:
            if "ffmpeg" in str(error).lower():
                _LOGGER.warning(
                    _(
                        "Video events are not supported unless ffmpeg is installed. Install FFMPEG on your system. Here is the error: "
                    )
                )
                _LOGGER.warning(_(error))
                os.remove(temp_vid.name)  # delete the temp file


class NewRoom(Event):
    """Event class to represent the creation of a new room."""

    def __init__(self, name=None, params=None, *args, **kwargs):  # noqa: D107
        super().__init__(*args, **kwargs)
        self.name = name
        self.room_params = params or {}


class RoomName(Event):
    """Event class to represent the naming of a room."""

    def __init__(self, name, *args, **kwargs):  # noqa: D107
        super().__init__(*args, **kwargs)
        self.name = name


class RoomAddress(Event):
    """Event class to represent a room's address being changed."""

    def __init__(self, address, *args, **kwargs):  # noqa: D107
        super().__init__(*args, **kwargs)
        self.address = address


class RoomImage(Event):
    """Event class to represent a room's display image being changed."""

    def __init__(self, room_image, *args, **kwargs):  # noqa: D107
        super().__init__(*args, **kwargs)
        if not isinstance(room_image, Image):
            raise TypeError(
                "Room image must be an opsdroid.events.Image instance"
            )  # pragma: no cover
        self.room_image = room_image


class RoomDescription(Event):
    """Event class to represent a room's description being changed."""

    def __init__(self, description, *args, **kwargs):  # noqa: D107
        super().__init__(*args, **kwargs)
        self.description = description


class JoinRoom(Event):
    """Event class to represent a user joining a room."""


class LeaveRoom(Event):
    """Event class to represent a user leaving a room."""


class UserInvite(Event):
    """Event class to represent a user being invited to a room."""


class UserRole(Event):
    """Event class to represent a user's role or powers in a room being changed."""

    def __init__(self, role, *args, **kwargs):  # noqa: D107
        super().__init__(*args, **kwargs)
        self.role = role


class JoinGroup(Event):
    """
    Event to represent joining a group (not a room).

    The group could be a slack team or a matrix community.
    """


class LeaveGroup(Event):
    """Even to represent leaving a group(not a room).

    The group could be a slack team, matrix community or a telegram group.
    """


class PinMessage(Event):
    """Event to represent pinning a message or other event."""


class UnpinMessage(Event):
    """Event to represent unpinning a message or other event."""


class DeleteMessage(Event):
    """Event to represent deleting a message or other event."""


class BanUser(Event):
    """Event to represent the banning of a user from a room."""
