import asynctest

from opsdroid.core import OpsDroid
from opsdroid.message import Message
from opsdroid.connector import Connector
from opsdroid.cli.start import configure_lang


class TestMessage(asynctest.TestCase):
    """Test the old opsdroid message class."""

    async def setup(self):
        configure_lang({})

    async def test_message(self):
        with OpsDroid() as opsdroid:
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

            self.assertEqual(message.text, "Hello world")
            self.assertEqual(message.user, "user")
            self.assertEqual(message.target, "default")
            self.assertEqual(message.raw_event["timestamp"], "01/01/2000 19:23:00")
            self.assertEqual(message.raw_event["messageId"], "101")
            with self.assertRaises(TypeError):
                await message.respond("Goodbye world")

    def test_depreacted_properties(self):
        message = Message(text="hello", user="user", room="", connector="")

        message.target = "spam"
        with self.assertWarns(DeprecationWarning):
            assert message.room == "spam"

        with self.assertWarns(DeprecationWarning):
            message.room = "eggs"

        assert message.room == "eggs"

        message.raw_event = "spam"
        with self.assertWarns(DeprecationWarning):
            assert message.raw_message == "spam"

        with self.assertWarns(DeprecationWarning):
            message.raw_message = "eggs"

        assert message.raw_event == "eggs"
