"""A base class for connectors to inherit from."""

from opsdroid.message import Message  # NOQA # pylint: disable=unused-import


class Connector():
    """A base connector.

    Connectors are used to interact with a given chat service.

    """

    def __init__(self, config):
        """Setup the connector.

        Set some basic properties from the connector config such as the name
        of this connector and the name the bot should appear with in chat
        service.

        Args:
            config (dict): The config for this connector specified in the
                           `configuration.yaml` file.

        """
        self.name = ""
        self.config = config

    def connect(self, opsdroid):
        """Connect to chat service and parse all messages.

        This method should block the thread with an infinite loop and create
        Message objects for chat messages coming from the service. It should
        then call `opsdroid.parse(message)` on those messages.

        Due to this method blocking, if multiple connectors are configured in
        opsdroid they will be run in parallel using the multiprocessing
        library.

        Args:
            opsdroid (OpsDroid): An instance of the opsdroid core.

        """
        raise NotImplementedError

    def respond(self, message):
        """Send a message back to the chat service.

        The message object will have a `text` property which should be sent
        back to the chat service. It may also have a `room` and `user` property
        which gives information on where the message should be directed.

        Args:
            message (Message): A message received by the connector.

        Returns:
            bool: True for message successfully sent. False otherwise.

        """
        raise NotImplementedError
