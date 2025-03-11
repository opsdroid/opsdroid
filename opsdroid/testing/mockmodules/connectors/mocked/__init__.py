"""A mocked connector module."""

from unittest.mock import AsyncMock

from opsdroid.connector import Connector, register_event
from opsdroid.events import Message


class ConnectorTest(Connector):
    """The mocked connector class."""

    def __init__(self, config, opsdroid=None):
        """Start the class."""
        self.name = "mocked"
        self.connect = AsyncMock()
        self.listen = AsyncMock()
        self.respond = AsyncMock()
        self.send = AsyncMock()
        self.disconnect = AsyncMock()
        self.opsdroid = AsyncMock()
        self.send_message = register_event(Message)(AsyncMock())
        super().__init__(config, opsdroid)

    @register_event(Message)
    async def send_message(self, message):
        """Send a Message."""
        pass
