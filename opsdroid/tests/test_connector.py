"""Test the opsdroid connector base class."""
import pytest
import asyncio

import asynctest.mock as amock

from opsdroid.core import OpsDroid
from opsdroid.connector import Connector, register_event
from opsdroid.events import Message, Reaction
from opsdroid.cli.start import configure_lang

configure_lang({})


@pytest.fixture(scope="session")
def loop():
    return asyncio.new_event_loop()


def test_init():
    config = {"example_item": "test"}
    connector = Connector(config, opsdroid=OpsDroid())
    assert connector.default_target is None
    assert connector.name == ""
    assert connector.config["example_item"] == "test"


def test_property():
    opsdroid = amock.CoroutineMock()
    connector = Connector({"name": "shell"}, opsdroid=opsdroid)
    assert connector.configuration.get("name") == "shell"


def test_connect(loop):
    connector = Connector({}, opsdroid=OpsDroid())
    with pytest.raises(NotImplementedError):
        loop.run_until_complete(connector.connect())


def test_listen(loop):
    connector = Connector({}, opsdroid=OpsDroid())
    with pytest.raises(NotImplementedError):
        loop.run_until_complete(connector.listen())


def test_respond(loop):
    connector = Connector({}, opsdroid=OpsDroid())
    with pytest.raises(TypeError):
        loop.run_until_complete(connector.send(Message("")))


def test_unsupported_event(loop):
    connector = Connector({}, opsdroid=OpsDroid())
    with pytest.raises(TypeError):
        loop.run_until_complete(connector.send(Reaction("emoji")))


def test_incorrect_event():
    class NotanEvent:
        pass

    class MyConnector(Connector):
        @register_event(NotanEvent)
        def send_my_event(self, event):
            pass

    with pytest.raises(TypeError):
        MyConnector()


def test_event_subclasses():
    class MyEvent(Message):
        pass

    class MyConnector(Connector):
        @register_event(Message, include_subclasses=True)
        def send_my_event(self, event):
            pass

    c = MyConnector({})
    assert MyEvent in c.events


"""Test the async methods of the opsdroid connector base class."""


async def setup():
    configure_lang({})


@pytest.mark.asyncio
async def test_disconnect():
    connector = Connector({}, opsdroid=OpsDroid())
    res = await connector.disconnect()
    assert res is None


@pytest.mark.asyncio
async def test_send_incorrect_event():
    connector = Connector({"name": "shell"})
    with pytest.raises(TypeError):
        await connector.send(object())


@pytest.mark.asyncio
async def test_dep_respond(recwarn):
    connector = Connector({"name": "shell"})
    with amock.patch("opsdroid.connector.Connector.send") as patched_send:
        await connector.respond("hello", room="bob")
        assert len(recwarn) == 3
        assert recwarn.pop(DeprecationWarning)

        patched_send.call_count == 1


@pytest.mark.asyncio
async def test_dep_react(recwarn):
    connector = Connector({"name": "shell"})

    with amock.patch("opsdroid.events.Message.respond") as patched_respond:
        await connector.react(Message("ori"), "hello")

        assert len(recwarn) == 3
        assert recwarn.pop(DeprecationWarning)
        assert recwarn.pop(DeprecationWarning)
        assert recwarn.pop(RuntimeWarning)

        patched_respond.call_count == 1


@pytest.mark.asyncio
async def test_depreacted_properties(recwarn):
    connector = Connector({"name": "shell"})

    connector.default_target = "spam"

    assert connector.default_room == "spam"
    assert len(recwarn) == 2
    assert recwarn.pop(DeprecationWarning)

    connector.default_room = "eggs"
    assert len(recwarn) == 2
    assert recwarn.pop(DeprecationWarning)

    assert connector.default_target == "eggs"
