"""A mocked connector module."""

from opsdroid.connector import Connector


class ConnectorTest(Connector):
    """The mocked connector class."""

    def __init__(self, config, opsdroid=None):
        """Start the class."""
        pass
