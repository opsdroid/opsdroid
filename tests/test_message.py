
import unittest
import unittest.mock as mock

from opsdroid.message import Message


class TestMessage(unittest.TestCase):
    """Test the opsdroid message class."""

    def test_message(self):
        mock_connector = mock.MagicMock()
        message = Message("Hello world", "user", "default", mock_connector)

        self.assertEqual(message.text, "Hello world")
        self.assertEqual(message.user, "user")
        self.assertEqual(message.room, "default")

        message.respond("Goodbye world")

        self.assertEqual(len(mock_connector.mock_calls), 1)

    def test_response_effects(self):
        """Responding to a message shouldn't change the message."""
        mock_connector = mock.MagicMock()
        message_text = "Hello world"
        message = Message(message_text, "user", "default", mock_connector)
        message.respond("Goodbye world")
        self.assertEqual(message_text, message.text)
