"""A mocked database module."""

from opsdroid.database import Database


class DatabaseTest(Database):
    """The mocked database class."""

    def __init__(self, config, opsdroid=None):
        """Start the class."""
        assert opsdroid is not None
        pass
