"""A mocked connector module."""

import unittest.mock as mock


class ConnectorTest:
    """The mocked connector class."""

    def __init__(self, config):
        """Start the class."""
        self.connect = mock.MagicMock()
        self.respond = mock.MagicMock()
