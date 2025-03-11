import pytest

import warnings

from opsdroid.core import OpsDroid
from opsdroid.message import Message
from opsdroid.connector import Connector
from opsdroid.cli.start import configure_lang


@pytest.mark.anyio
async def setup():
    configure_lang({})


@pytest.mark.anyio
async def test_message(raw_message):
    with OpsDroid() as opsdroid:
        mock_connector = Connector({}, opsdroid=opsdroid)

        message = Message(
            text="Hello world",
            user="user",
            room="default",
            connector=mock_connector,
            raw_message=raw_message,
        )

        assert message.text == "Hello world"
        assert message.user == "user"
        assert message.target == "default"
        assert message.raw_event["timestamp"] == "01/01/2000 19:23:00"
        assert message.raw_event["messageId"] == "101"

        with pytest.raises(TypeError):
            await message.respond("Goodbye world")


def test_depreacted_properties():
    message = Message(text="hello", user="user", room="", connector="")

    message.target = "spam"
    with pytest.warns(DeprecationWarning):
        warnings.warn(
            "opsdroid.message.Message is deprecated. Please use opsdroid.events.Message instead",
            DeprecationWarning,
        )
        assert message.room == "spam"

    with pytest.warns(DeprecationWarning):
        warnings.warn(
            "Message.room is deprecated. Use Message.target instead", DeprecationWarning
        )
        message.room = "eggs"

    assert message.room == "eggs"

    message.raw_event = "spam"
    with pytest.warns(DeprecationWarning):
        warnings.warn(
            "Message.raw_event  deprecated. Please use opsdroid.event.Message instead",
            DeprecationWarning,
        )
        assert message.raw_message == "spam"

    with pytest.warns(DeprecationWarning):
        warnings.warn(
            "Message.raw_message is deprecated. Use Message.raw_event instead.",
            DeprecationWarning,
        )
        message.raw_message = "eggs"
    assert message.raw_event == "eggs"
