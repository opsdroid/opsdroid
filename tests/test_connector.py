import unittest
import asyncio

import asynctest
import asynctest.mock as amock

from opsdroid.__main__ import configure_lang
from opsdroid.core import OpsDroid
from opsdroid.connector import Connector, register_event
from opsdroid.events import Event, Message, Reaction
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

    def test_incorrect_event(self):
        class NotanEvent:
            pass

        class MyConnector(Connector):
            @register_event(NotanEvent)
            def send_my_event(self, event):
                pass

        with self.assertRaises(TypeError):
            MyConnector()

    def test_event_subclasses(self):
        class MyEvent(Message):
            pass

        class MyConnector(Connector):
            @register_event(Message, include_subclasses=True)
            def send_my_event(self, event):
                pass

        MyConnector({})

class TestConnectorAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid connector base class."""

    async def setup(self):
        configure_lang({})

    async def test_disconnect(self):
        connector = Connector({}, opsdroid=OpsDroid())
        res = await connector.disconnect()
        assert res is None

    async def test_send_incorrect_event(self):
        connector = Connector({"name": "shell"})
        with self.assertRaises(TypeError):
            await connector.send(object())

    async def test_dep_respond(self):
        connector = Connector({"name": "shell"})
        with amock.patch("opsdroid.connector.Connector.send") as patched_send:
            with self.assertWarns(DeprecationWarning):
                await connector.respond("hello", room="bob")

            patched_send.call_count == 1

    async def test_dep_react(self):
        connector = Connector({"name": "shell"})
        with amock.patch("opsdroid.events.Message.respond") as patched_respond:
            with self.assertWarns(DeprecationWarning):
                await connector.react(Message("ori"), "hello")

            patched_respond.call_count == 1

    async def test_depreacted_properties(self):
        connector = Connector({"name": "shell"})

        connector.default_target = "spam"
        with self.assertWarns(DeprecationWarning):
            assert connector.default_room == "spam"

        with self.assertWarns(DeprecationWarning):
            connector.default_room = "eggs"

        assert connector.default_target == "eggs"
