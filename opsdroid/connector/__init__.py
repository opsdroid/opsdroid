"""A base class for connectors to inherit from."""

import logging
from opsdroid.message import Message  # NOQA # pylint: disable=unused-import


_LOGGER = logging.getLogger(__name__)


class Connector():
    """A base connector.

    Connectors are used to interact with a given chat service.

    """

    def __init__(self, config):
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

    @property
    def configuration(self):
        """Class property used to access the connector config."""
        return self.config

    async def connect(self, opsdroid):
        """Connect to chat service.

        This method should create a connection to the desired chat service.
        It should also be possible to call it multiple times in the event of
        being disconnected.

        Args:
            opsdroid (OpsDroid): An instance of the opsdroid core.

        """
        raise NotImplementedError

    async def listen(self, opsdroid):
        """Listen to chat service and parse all messages.

        This method should block the thread with an infinite loop and create
        Message objects for chat messages coming from the service. It should
        then call `await opsdroid.parse(message)` on those messages.

        As the method should include some kind of `while True` all messages
        from the chat service should be "awaited" asyncronously to avoid
        blocking the thread.

        Args:
            opsdroid (OpsDroid): An instance of the opsdroid core.

        """
        raise NotImplementedError

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
        raise NotImplementedError

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
        _LOGGER.debug(_("%s connector can't react to messages"), self.name)
        return False

    async def user_typing(self, opsdroid, trigger):
        """Signals that opsdroid is typing.

        Args:
            opsdroid (OpsDroid): An instance of the opsdroid core.
            trigger: a bool that allows the event to be triggered on/off

        Triggers the "user is typing" event if the chat service that
        opsdroid is connected to accepts it.
        """
        pass

    async def disconnect(self, opsdroid):
        """Disconnect from the chat service.

        This method is called when opsdroid is exiting, it can be used to close
        connections or do other cleanup.

        Args:
            opsdroid (OpsDroid): An instance of the opsdroid core.

        """
        pass
