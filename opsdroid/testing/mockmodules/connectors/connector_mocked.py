"""A mocked connector module."""

import asynctest.mock as amock

from opsdroid.connector import Connector


class ConnectorTest(Connector):
    """The mocked connector class."""

    def __init__(self, config, opsdroid=None):
        """Start the class."""
        self.connect = amock.CoroutineMock()
        self.listen = amock.CoroutineMock()
        self.respond = amock.CoroutineMock()
        self.disconnect = amock.CoroutineMock()
        self.opsdroid = amock.CoroutineMock()
