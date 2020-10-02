import pytest

import asynctest.mock as amock

from opsdroid.connector import Connector, register_event
from opsdroid.events import Message, Reaction


class TestConnectorBaseClass:
    """Test the opsdroid connector base class."""

    def test_init(self, opsdroid):
        config = {"example_item": "test"}
        connector = Connector(config, opsdroid=opsdroid)
        assert connector.default_target is None
        assert connector.name == ""
        assert connector.config["example_item"] == "test"

    def test_property(self):
        opsdroid = amock.CoroutineMock()
        connector = Connector({"name": "shell"}, opsdroid=opsdroid)
        assert connector.configuration.get("name") == "shell"

    def test_connect(self, event_loop, no_config_connector):
        with pytest.raises(NotImplementedError):
            event_loop.run_until_complete(no_config_connector.connect())

    def test_listen(self, event_loop, no_config_connector):
        with pytest.raises(NotImplementedError):
            event_loop.run_until_complete(no_config_connector.listen())

    def test_respond(self, event_loop, no_config_connector):
        with pytest.raises(TypeError):
            event_loop.run_until_complete(no_config_connector.send(Message("")))

    def test_unsupported_event(self, event_loop, no_config_connector):
        with pytest.raises(TypeError):
            event_loop.run_until_complete(no_config_connector.send(Reaction("emoji")))

    def test_incorrect_event(self):
        class NotanEvent:
            pass

        class MyConnector(Connector):
            @register_event(NotanEvent)
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

        c = MyConnector({})
        assert MyEvent in c.events


class TestConnectorAsync:
    """Test the async methods of the opsdroid connector base class."""

    @pytest.mark.asyncio
    async def test_disconnect(self, no_config_connector):
        res = await no_config_connector.disconnect()
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

            patched_send.call_count == 1

    @pytest.mark.asyncio
    async def test_dep_react(self, recwarn):
        connector = Connector({"name": "shell"})

        with amock.patch("opsdroid.events.Message.respond") as patched_respond:
            await connector.react(Message("ori"), "hello")

            assert len(recwarn) >= 1
            assert recwarn.pop(DeprecationWarning)

            patched_respond.call_count == 1

    @pytest.mark.asyncio
    async def test_depreacted_properties(self, recwarn):
        connector = Connector({"name": "shell"})

        connector.default_target = "spam"
        assert connector.default_room == "spam"

        assert len(recwarn) >= 1
        assert recwarn.pop(DeprecationWarning)

        connector.default_room = "eggs"
        assert connector.default_target == "eggs"

        assert len(recwarn) >= 1
        assert recwarn.pop(DeprecationWarning)
