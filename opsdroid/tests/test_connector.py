import pytest

import asynctest.mock as amock

from opsdroid.connector import Connector, register_event
from opsdroid.events import Message, Reaction


class TestConnectorBaseClass:
    """Test the opsdroid connector base class."""

    def test_init(self, opsdroid, get_connector):
        connector = get_connector(config={"example_item": "test"})
        assert connector.default_target is None
        assert connector.name == ""
        assert connector.config["example_item"] == "test"

    def test_property(self, get_connector):
        connector = get_connector(config={"name": "shell"})
        assert connector.configuration.get("name") == "shell"

    def test_connect(self, event_loop, get_connector):
        with pytest.raises(NotImplementedError):
            event_loop.run_until_complete(get_connector().connect())

    def test_listen(self, event_loop, get_connector):
        with pytest.raises(NotImplementedError):
            event_loop.run_until_complete(get_connector().listen())

    def test_respond(self, event_loop, get_connector):
        with pytest.raises(TypeError):
            event_loop.run_until_complete(get_connector().send(Message("")))

    def test_unsupported_event(self, event_loop, get_connector):
        with pytest.raises(TypeError):
            event_loop.run_until_complete(get_connector().send(Reaction("emoji")))

    def test_incorrect_event(self):
        class NotAnEvent:
            pass

        class MyConnector(Connector):
            @register_event(NotAnEvent)
            def send_my_event(self, event):
                pass

        with pytest.raises(TypeError):
            MyConnector()

    def test_event_subclasses(self):
        class MyEvent(Message):
            pass

        class MyConnector(Connector):
            @register_event(Message, include_subclasses=True)
            def send_my_event(self, event):
                pass

        connector = MyConnector({})
        assert MyEvent in connector.events


class TestConnectorAsync:
    """Test the async methods of the opsdroid connector base class."""

    @pytest.mark.asyncio
    async def test_disconnect(self, get_connector):
        res = await get_connector().disconnect()
        assert res is None

    @pytest.mark.asyncio
    async def test_send_incorrect_event(self):
        connector = Connector({"name": "shell"})
        with pytest.raises(TypeError):
            await connector.send(object())

    @pytest.mark.asyncio
    async def test_dep_respond(self, recwarn):
        connector = Connector({"name": "shell"})
        with amock.patch("opsdroid.connector.Connector.send") as patched_send:
            await connector.respond("hello", room="bob")

            assert len(recwarn) >= 1
            assert recwarn.pop(DeprecationWarning)

            assert patched_send.call_count == 1

    @pytest.mark.asyncio
    async def test_dep_react(self, get_connector, recwarn):
        connector = get_connector({"name": "shell"})

        with amock.patch("opsdroid.events.Message.respond") as patched_respond:
            await connector.react(Message("ori"), "hello")

            assert len(recwarn) >= 1
            assert recwarn.pop(DeprecationWarning)

            assert patched_respond.call_count == 1

    @pytest.mark.asyncio
    async def test_deprecated_properties(self, get_connector, recwarn):
        connector = get_connector({"name": "shell"})

        connector.default_target = "spam"
        assert connector.default_room == "spam"

        assert len(recwarn) >= 1
        assert recwarn.pop(DeprecationWarning)

        connector.default_room = "eggs"
        assert connector.default_target == "eggs"

        assert len(recwarn) >= 1
        assert recwarn.pop(DeprecationWarning)
