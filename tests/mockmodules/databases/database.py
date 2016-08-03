"""A mocked database module."""

import unittest.mock as mock


class DatabaseTest:
    """The mocked database class."""

    def __init__(self, config):
        """Start the class."""
        self.connect = mock.MagicMock()
