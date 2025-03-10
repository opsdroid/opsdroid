"""A mocked connector module."""

from unittest.mock import AsyncMock

from opsdroid.connector import Connector


class ConnectorTest(Connector):
    """The mocked connector class."""

    def __init__(self, config, opsdroid=None):
        """Start the class."""
        self.connect = AsyncMock()
        self.listen = AsyncMock()
        self.respond = AsyncMock()
        self.disconnect = AsyncMock()
        self.opsdroid = AsyncMock()
