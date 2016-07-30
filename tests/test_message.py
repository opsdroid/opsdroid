
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
        self.assertEqual(message.text, "Goodbye world")
