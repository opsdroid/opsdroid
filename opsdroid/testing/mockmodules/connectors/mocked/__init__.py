"""A mocked connector module."""

import asynctest.mock as amock

from opsdroid.connector import Connector, register_event
from opsdroid.events import Message


class ConnectorTest(Connector):
    """The mocked connector class."""

    def __init__(self, config, opsdroid=None):
        """Start the class."""
        self.name = "mocked"
        self.connect = amock.CoroutineMock()
        self.listen = amock.CoroutineMock()
        self.respond = amock.CoroutineMock()
        self.disconnect = amock.CoroutineMock()
        self.opsdroid = amock.CoroutineMock()
        self.send_message = register_event(Message)(amock.CoroutineMock())
        super().__init__(config, opsdroid)

    @register_event(Message)
    async def send_message(self, message):
        """Send a Message."""
        pass
