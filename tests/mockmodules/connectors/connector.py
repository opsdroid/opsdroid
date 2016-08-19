"""A mocked connector module."""

import unittest.mock as mock

from opsdroid.connector import Connector


class ConnectorTest(Connector):
    """The mocked connector class."""

    def __init__(self, config):
        """Start the class."""
        self.connect = mock.MagicMock()
        self.respond = mock.MagicMock()
