"""A base class for connectors to inherit from."""

import collections
import inspect
import logging

from opsdroid.events import Event


_LOGGER = logging.getLogger(__name__)


__all__ = ['Connector', 'register_event']


def register_event(event_type):
    """
    Register a method to handle a specific `opsdroid.events.Event` object.

    Args:
        event (Event): The event class this method can handle.
    """
    def decorator(func):
        func.__opsdroid_event__ = event_type
        return func
    return decorator


class Connector:
    """A base connector.

    Connectors are used to interact with a given chat service.

    """
    def __new__(cls, *args, **kwargs):
        """
        Before constructing the class parse all the methods that have been
        decorated with ``register_event``.
        """

        # Get all 'function' members as the wrapped methods are functions
        # This returns a tuple of (name, function) for each method.
        functions = inspect.getmembers(cls, predicate=inspect.isfunction)

        # Filter out anything that's not got the attribute __opsdroid_event__
        event_methods = filter(lambda f: hasattr(f, "__opsdroid_event__"),
                               # Just extract the function objects
                               map(lambda t: t[1], functions))

        # If we don't have the event call the unknown event coroutine
        cls.events = collections.defaultdict(lambda: cls._unknown_event)

        for event_method in event_methods:
            event_type = event_method.__opsdroid_event__

            if not issubclass(event_type, Event):
                raise TypeError(f"The event type {event_type} is not"
                                " a valid OpsDroid event type")

            cls.events[event_type] = event_method

        return super().__new__(cls, *args, **kwargs)

    def __init__(self, config, opsdroid=None):
        """Create the connector.

        Set some basic properties from the connector config such as the name
        of this connector and the name the bot should appear with in chat
        service.

        Args:
            config (dict): The config for this connector specified in the
                           `configuration.yaml` file.

        """
        self.name = ""
        self.config = config
        self.default_room = None
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
        """
        This is the fallback function that is called if the subclass can not
        handle the event type.
        """
        raise TypeError(
            "Connector {type(self)} can not handle the"
            " '{type(event).__name__}' event type.".format(self=self,
                                                           event=event))

    async def send(self, event, target=None):
        """Send a message to the chat service.

        Args:
            event (Event): A message received by the connector.
            target (string): The name of the room or other place to send the
            event.

        Returns:
            bool: True for event successfully sent. False otherwise.
        """
        return await self.events[type(event)](self, event, target=target)

    async def disconnect(self):
        """Disconnect from the chat service.

        This method is called when opsdroid is exiting, it can be used to close
        connections or do other cleanup.
        """
