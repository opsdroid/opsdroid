from opsdroid.message import Message
from opsdroid.connector import Connector
from opsdroid.cli.start import configure_lang

import pytest

configure_lang({})


async def test_message(opsdroid):
    mock_connector = Connector({}, opsdroid=opsdroid)
    raw_message = {
        "text": "Hello world",
        "user": "user",
        "room": "default",
        "timestamp": "01/01/2000 19:23:00",
        "messageId": "101",
    }
    message = Message(
        text="Hello world",
        user="user",
        room="default",
        connector=mock_connector,
        raw_message=raw_message,
    )

    assert message.text == "Hello world"
    assert message.user == "user"
    assert message.room == "default"
    assert message.raw_event["timestamp"] == "01/01/2000 19:23:00"
    assert message.raw_event["messageId"] == "101"

    with pytest.raises(TypeError):
        await message.respond("Goodbye world")


def test_depreacted_properties():
    message = Message(text="hello", user="user", room="", connector="")

    message.target = "spam"

    with pytest.warns(DeprecationWarning):
        assert message.room == "spam"

    with pytest.warns(DeprecationWarning):
        message.room = "eggs"

    assert message.room == "eggs"

    message.raw_event = "spam"
    with pytest.warns(DeprecationWarning):
        assert message.raw_event == "spam"

    with pytest.warns(DeprecationWarning):
        message.raw_event = "eggs"

    assert message.raw_event == "eggs"
