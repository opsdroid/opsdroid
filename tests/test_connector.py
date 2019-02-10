import unittest
import asyncio

import asynctest
import asynctest.mock as amock

from opsdroid.__main__ import configure_lang
from opsdroid.core import OpsDroid
from opsdroid.connector import Connector
from opsdroid.events import Message, Typing, Reaction
from opsdroid.__main__ import configure_lang


class TestConnectorBaseClass(unittest.TestCase):
    """Test the opsdroid connector base class."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        configure_lang({})

    def test_init(self):
        config = {"example_item": "test"}
        connector = Connector(config, opsdroid=OpsDroid())
        self.assertEqual(None, connector.default_target)
        self.assertEqual("", connector.name)
        self.assertEqual("test", connector.config["example_item"])

    def test_property(self):
        opsdroid = amock.CoroutineMock()
        connector = Connector({"name": "shell"}, opsdroid=opsdroid)
        self.assertEqual("shell", connector.configuration.get("name"))

    def test_connect(self):
        connector = Connector({}, opsdroid=OpsDroid())
        with self.assertRaises(NotImplementedError):
            self.loop.run_until_complete(connector.connect())

    def test_listen(self):
        connector = Connector({}, opsdroid=OpsDroid())
        with self.assertRaises(NotImplementedError):
            self.loop.run_until_complete(connector.listen())

    def test_respond(self):
        connector = Connector({}, opsdroid=OpsDroid())
        with self.assertRaises(TypeError):
            self.loop.run_until_complete(connector.send(Message("")))

    def test_unsupported_event(self):
        connector = Connector({}, opsdroid=OpsDroid())
        with self.assertRaises(TypeError):
            self.loop.run_until_complete(connector.send(Reaction("emoji")))


class TestConnectorAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid connector base class."""
    async def setup(self):
        configure_lang({})

    async def test_disconnect(self):
        connector = Connector({}, opsdroid=OpsDroid())
        res = await connector.disconnect()
        assert res is None
