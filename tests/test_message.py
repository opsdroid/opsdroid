
import asynctest
import asynctest.mock as amock

from opsdroid.message import Message
from opsdroid.connector import Connector


class TestMessage(asynctest.TestCase):
    """Test the opsdroid message class."""

    async def test_message(self):
        mock_connector = Connector({})
        raw_message = {
            'text': 'Hello world',
            'user': 'user',
            'room': 'default',
            'timestamp': '01/01/2000 19:23:00',
            'messageId': '101'
        }
        message = Message(
            "Hello world",
            "user",
            "default",
            mock_connector,
            raw_message)

        self.assertEqual(message.text, "Hello world")
        self.assertEqual(message.user, "user")
        self.assertEqual(message.room, "default")
        self.assertEqual(
            message.raw_message['timestamp'], '01/01/2000 19:23:00'
            )
        self.assertEqual(message.raw_message['messageId'], '101')
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

    async def test_thinking_sleep(self):
        mock_connector_int = Connector({
            'name': 'shell',
            'thinking-delay': 3,
            'type': 'connector',
            'module_path': 'opsdroid-modules.connector.shell'
        })

        with amock.patch('asyncio.sleep') as mocksleep_int:
            message = Message("hi", "user", "default", mock_connector_int)
            with self.assertRaises(NotImplementedError):
                await message.respond("Hello there")

            self.assertTrue(mocksleep_int.called)

        # Test thinking-delay with a list

        mock_connector_list = Connector({
            'name': 'shell',
            'thinking-delay': [1, 4],
            'type': 'connector',
            'module_path': 'opsdroid-modules.connector.shell'
        })

        with amock.patch('asyncio.sleep') as mocksleep_list:
            message = Message("hi", "user", "default", mock_connector_list)
            with self.assertRaises(NotImplementedError):
                await message.respond("Hello there")

            self.assertTrue(mocksleep_list.called)

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

    async def test_typing_sleep(self):
        mock_connector = Connector({
            'name': 'shell',
            'typing-delay': 6,
            'type': 'connector',
            'module_path': 'opsdroid-modules.connector.shell'
        })
        with amock.patch('asyncio.sleep') as mocksleep:
            message = Message("hi", "user", "default", mock_connector)
            with self.assertRaises(NotImplementedError):
                await message.respond("Hello there")

            self.assertTrue(mocksleep.called)

    async def test_react(self):
        mock_connector = Connector({
            'name': 'shell',
            'thinking-delay': 2,
            'type': 'connector',
        })
        with amock.patch('asyncio.sleep') as mocksleep:
            message = Message("Hello world", "user", "default", mock_connector)
            reacted = await message.react("emoji")
            self.assertTrue(mocksleep.called)
            self.assertFalse(reacted)
