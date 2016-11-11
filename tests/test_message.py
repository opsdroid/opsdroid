
import asynctest

from opsdroid.message import Message
from opsdroid.connector import Connector


class TestMessage(asynctest.TestCase):
    """Test the opsdroid message class."""

    async def test_message(self):
        mock_connector = Connector({})
        message = Message("Hello world", "user", "default", mock_connector)

        self.assertEqual(message.text, "Hello world")
        self.assertEqual(message.user, "user")
        self.assertEqual(message.room, "default")
        with self.assertRaises(NotImplementedError):
            await message.respond("Goodbye world")

    async def test_response_effects(self):
        """Responding to a message shouldn't change the message."""
        mock_connector = Connector({})
        message_text = "Hello world"
        message = Message(message_text, "user", "default", mock_connector)
        with self.assertRaises(NotImplementedError):
            await message.respond("Goodbye world")
        self.assertEqual(message_text, message.text)
