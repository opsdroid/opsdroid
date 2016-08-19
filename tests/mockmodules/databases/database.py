"""A mocked database module."""

import unittest.mock as mock

from opsdroid.database import Database


class DatabaseTest(Database):
    """The mocked database class."""

    def __init__(self, config):
        """Start the class."""
        self.connect = mock.MagicMock()
