"""Tests for the ConnectorSlack class."""
import asyncio

import unittest
import unittest.mock as mock
import asynctest
import asynctest.mock as amock

from opsdroid.core import OpsDroid
from opsdroid.connector.ciscospark import ConnectorCiscoSpark
from opsdroid.events import Message, Reaction
from opsdroid.__main__ import configure_lang


class TestConnectorCiscoSpark(unittest.TestCase):
    """Test the opsdroid CiscoSpark connector class."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        configure_lang({})

    def test_init(self):
        """Test that the connector is initialised properly."""
        connector = ConnectorCiscoSpark({})
        self.assertEqual("ciscospark", connector.name)
        self.assertEqual("opsdroid", connector.bot_name)

    def test_missing_api_key(self):
        """Test that creating without an API without config raises an error."""
        with self.assertRaises(TypeError):
            ConnectorCiscoSpark()
