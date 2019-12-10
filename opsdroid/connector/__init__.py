"""A base class for connectors to inherit from."""

import collections
import inspect
import logging
import warnings

from opsdroid.events import Event, Reaction, Message


_LOGGER = logging.getLogger(__name__)


__all__ = ["Connector", "register_event"]


def register_event(event_type, include_subclasses=False):
    """
    Register a method to handle a specific `opsdroid.events.Event` object.

    Args:
        event_type (Event): The event class this method can handle.
        include_subclasses (bool): Allow the function to trigger on subclasses of the registered
            event. Defaults to False.

    """

    def decorator(func):
        if hasattr(func, "__opsdroid_events__"):
            func.__opsdroid_events__.append(event_type)
        else:
            func.__opsdroid_events__ = [event_type]

        func.__opsdroid_match_subclasses__ = include_subclasses
        return func

    return decorator


class Connector:
    """A base connector.

    Connectors are used to interact with a given chat service.

    """

    def __new__(cls, *args, **kwargs):
        """Create the class object.

        Before constructing the class parse all the methods that have been
        decorated with ``register_event``.
        """
        # Get all 'function' members as the wrapped methods are functions
        # This returns a tuple of (name, function) for each method.
        functions = inspect.getmembers(cls, predicate=inspect.isfunction)

        # Filter out anything that's not got the attribute __opsdroid_event__
        event_methods = filter(
            lambda f: hasattr(f, "__opsdroid_events__"),
            # Just extract the function objects
            map(lambda t: t[1], functions),
        )

        # If we don't have the event call the unknown event coroutine
        cls.events = collections.defaultdict(lambda: cls._unknown_event)

        for event_method in event_methods:
            for event_type in event_method.__opsdroid_events__:
                if not issubclass(event_type, Event):
                    err_msg = (
                        "The event type {event_type} is "
                        "not a valid OpsDroid event type"
                    )
                    raise TypeError(err_msg.format(event_type=event_type))

                if event_method.__opsdroid_match_subclasses__:
                    # Register all event types which are a subclass of this
                    # one.
                    for event in Event.event_registry.values():
                        if issubclass(event, event_type):
                            cls.events[event] = event_method
                else:
                    cls.events[event_type] = event_method

        return super().__new__(cls)

    def __init__(self, config, opsdroid=None):
        """Create the connector.

        Set some basic properties from the connector config such as the name
        of this connector and the name the bot should appear with in chat
        service.

        Args:
            config (dict): The config for this connector specified in the
                           `configuration.yaml` file.
            opsdroid (OpsDroid): An instance of opsdroid.core.

        """
        self.name = ""
        self.config = config
        self.default_target = None
        self.opsdroid = opsdroid

    @property
    def configuration(self):
        """Class property used to access the connector config."""
        return self.config

    async def connect(self):
        """Connect to chat service.

        This method should create a connection to the desired chat service.
        It should also be possible to call it multiple times in the event of
        being disconnected.

        """
        raise NotImplementedError

    async def listen(self):
        """Listen to chat service and parse all messages.

        This method should block the thread with an infinite loop and create
        Message objects for chat messages coming from the service. It should
        then call `await opsdroid.parse(message)` on those messages.

        As the method should include some kind of `while True` all messages
        from the chat service should be "awaited" asyncronously to avoid
        blocking the thread.
        """
        raise NotImplementedError

    async def _unknown_event(self, event, target=None):
        """Fallback for when the subclass can not handle the event type."""
        raise TypeError(
            "Connector {stype} can not handle the"
            " '{eventt.__name__}' event type.".format(
                stype=type(self), eventt=type(event)
            )
        )

    async def respond(self, message, room=None):
        """Send a message back to the chat service.

        The message object will have a `text` property which should be sent
        back to the chat service. It may also have a `room` and `user` property
        which gives information on where the message should be directed.

        Args:
            message (Message): A message received by the connector.
            room (string): Name of the room to send the message to

        Returns:
            bool: True for message successfully sent. False otherwise.

        """
        warnings.warn(
            "Connector.respond is deprecated. Use " "Connector.send instead.",
            DeprecationWarning,
        )

        if isinstance(message, str):
            message = Message(message)

        if room:
            message.target = room

        return await self.send(message)

    async def disconnect(self):
        """Disconnect from the chat service.

        This method is called when opsdroid is exiting, it can be used to close
        connections or do other cleanup.
        """

    async def react(self, message, emoji):
        """React to a message.

        Not all connectors will have capabilities to react messages, so this
        method don't have to be implemented and by default logs a debug message
        and returns False.

        Args:
            message (Message): A message received by the connector.
            emoji    (string): The emoji name with which opsdroid will react

        Returns:
            bool: True for message successfully sent. False otherwise.

        """
        warnings.warn(
            "Connector.react is deprecated. Use "
            "Connector.send(events.Reaction(emoji)) instead.",
            DeprecationWarning,
        )

        return await message.respond(Reaction(emoji))

    async def send(self, event):
        """Send a message to the chat service.

        Args:
            event (Event): A message received by the connector.
            target (string): The name of the room or other place to send the
            event.

        Returns:
            bool: True for event successfully sent. False otherwise.

        """
        if not isinstance(event, Event):
            raise TypeError(
                "The event argument to send must be an opsdroid Event object"
            )

        # If the event does not have a target, use the default.
        event.target = event.target or self.default_target

        return await self.events[type(event)](self, event)

    @property
    def default_room(self):  # noqa: D401
        """The room to send messages to if not specified."""
        warnings.warn(
            "Connector.default_room is deprecated. Use "
            "Connector.default_target instead.",
            DeprecationWarning,
        )

        return self.default_target

    @default_room.setter
    def default_room(self, value):
        warnings.warn(
            "Connector.default_room is deprecated. Use "
            "Connector.default_target instead.",
            DeprecationWarning,
        )

        self.default_target = value
