
import asynctest
import asynctest.mock as amock

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

    async def test_thinking_delay(self):
        mock_connector = Connector({
            'name': 'shell',
            'thinking-delay': 3,
            'type': 'connector',
            'module_path': 'opsdroid-modules.connector.shell'
        })

        with amock.patch(
                'opsdroid.message.Message._thinking_delay') as logmock:
            message = Message("hi", "user", "default", mock_connector)
            with self.assertRaises(NotImplementedError):
                await message.respond("Hello there")

            self.assertTrue(logmock.called)

    async def test_typing_delay(self):
        mock_connector = Connector({
            'name': 'shell',
            'typing-delay': 6,
            'type': 'connector',
            'module_path': 'opsdroid-modules.connector.shell'
        })
        with amock.patch(
                'opsdroid.message.Message._typing_delay') as logmock:
            with amock.patch('asyncio.sleep') as mocksleep:
                message = Message("hi", "user", "default", mock_connector)
                with self.assertRaises(NotImplementedError):
                    await message.respond("Hello there")

                self.assertTrue(logmock.called)
                self.assertTrue(mocksleep.called)
