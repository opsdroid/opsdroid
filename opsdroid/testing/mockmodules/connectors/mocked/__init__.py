"""A mocked connector module."""

import unittest.mock as amock

from opsdroid.connector import Connector, register_event
from opsdroid.events import Message


class ConnectorTest(Connector):
    """The mocked connector class."""

    def __init__(self, config, opsdroid=None):
        """Start the class."""
        self.name = "mocked"
        self.connect = amock.AsyncMock()
        self.listen = amock.AsyncMock()
        self.respond = amock.AsyncMock()
        self.send = amock.AsyncMock()
        self.disconnect = amock.AsyncMock()
        self.opsdroid = amock.AsyncMock()
        self.send_message = register_event(Message)(amock.AsyncMock())
        super().__init__(config, opsdroid)

    @register_event(Message)
    async def send_message(self, message):
        """Send a Message."""
        pass
