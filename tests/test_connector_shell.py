"""Tests for the ConnectorShell class."""
import asyncio

import unittest
import unittest.mock as mock
import asynctest
import asynctest.mock as amock
#import shell ??

from opsdroid.core import OpsDroid
from opsdroid.connector.shell import ConnectorShell
from opsdroid.events import Message, Reaction
from opsdroid.cli.start import configure_lang

class TestConnectorShell(unittest.TestCase):
    """Test the opsdroid Shell connector class."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        configure_lang({})

    def test_init(self):
        """Test that the connector is initialised properly."""
        connector = ConnectorShell({}, opsdroid=OpsDroid())
        self.assertEqual("opsdroid", connector.bot_name)
        self.assertEqual("shell", connector.name)

    def test_draw_prompt(self):
        pass
    
    def test_clear_prompt(self):
        pass
    

class TestConnectorShellAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid Shell connector class."""

    async def setUp(self):
        configure_lang({})

    async def test_read_stdin(self):
        pass

    async def test_async_input(self):
        pass
    
    async def test__parse_message(self):
        pass
    
    async def test_connect(self):
        pass
    
    async def test_listen(self):
        pass
    
    async def test_respond(self):
        pass
    
    async def test_disconnect(self):
        pass
    