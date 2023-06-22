"""A mocked connector module."""

import unittest.mock as amock

from opsdroid.connector import Connector


class ConnectorTest(Connector):
    """The mocked connector class."""

    def __init__(self, config, opsdroid=None):
        """Start the class."""
        self.connect = amock.AsyncMock()
        self.listen = amock.AsyncMock()
        self.respond = amock.AsyncMock()
        self.disconnect = amock.AsyncMock()
        self.opsdroid = amock.AsyncMock()
