from unittest import mock

import asynctest
import asynctest.mock as amock

from opsdroid import events
from opsdroid.core import OpsDroid
from opsdroid.connector import Connector
from opsdroid.__main__ import configure_lang


class TestEvent(asynctest.TestCase):
    """Test the opsdroid event class."""

    async def setup(self):
        configure_lang({})

    async def test_event(self):
        opsdroid = amock.CoroutineMock()
        mock_connector = Connector({}, opsdroid=opsdroid)
        event = events.Event(
            "user",
            "default",
            mock_connector)

        self.assertEqual(event.user, "user")
        self.assertEqual(event.target, "default")


class TestMessage(asynctest.TestCase):
    """Test the opsdroid message class."""

    async def setup(self):
        configure_lang({})

    async def test_message(self):
        with OpsDroid() as opsdroid:
            mock_connector = Connector({}, opsdroid=opsdroid)
            raw_message = {
                'text': 'Hello world',
                'user': 'user',
                'room': 'default',
                'timestamp': '01/01/2000 19:23:00',
                'messageId': '101'
            }
            message = events.Message(
                "Hello world",
                "user",
                "default",
                mock_connector,
                raw_event=raw_message)

            self.assertEqual(message.text, "Hello world")
            self.assertEqual(message.user, "user")
            self.assertEqual(message.target, "default")
            self.assertEqual(
                message.raw_event['timestamp'], '01/01/2000 19:23:00'
                )
            self.assertEqual(message.raw_event['messageId'], '101')
            with self.assertRaises(TypeError):
                await message.respond("Goodbye world")
            # Also try responding with just some empty Event
            with self.assertRaises(TypeError):
                await message.respond(events.Event(
                    message.user, message.target, message.connector))

    async def test_response_effects(self):
        """Responding to a message shouldn't change the message."""
        with OpsDroid() as opsdroid:
            mock_connector = Connector({}, opsdroid=opsdroid)
            message_text = "Hello world"
            message = events.Message(message_text, "user", "default", mock_connector)
            with self.assertRaises(TypeError):
                await message.respond("Goodbye world")
            self.assertEqual(message_text, message.text)

    async def test_thinking_delay(self):
        with OpsDroid() as opsdroid:
            mock_connector = Connector({
                'name': 'shell',
                'thinking-delay': 3,
                'type': 'connector',
                'module_path': 'opsdroid-modules.connector.shell'
            }, opsdroid=opsdroid)

            with amock.patch(
                    'opsdroid.events.Message._thinking_delay') as logmock:
                message = events.Message("hi", "user", "default", mock_connector)
                with self.assertRaises(TypeError):
                    await message.respond("Hello there")

                self.assertTrue(logmock.called)

    async def test_thinking_sleep(self):
        with OpsDroid() as opsdroid:
            mock_connector_int = Connector({
                'name': 'shell',
                'thinking-delay': 3,
                'type': 'connector',
                'module_path': 'opsdroid-modules.connector.shell'
            }, opsdroid=opsdroid)

            with amock.patch('asyncio.sleep') as mocksleep_int:
                message = events.Message("hi", "user", "default", mock_connector_int)
                with self.assertRaises(TypeError):
                    await message.respond("Hello there")

                self.assertTrue(mocksleep_int.called)

            # Test thinking-delay with a list

            mock_connector_list = Connector({
                'name': 'shell',
                'thinking-delay': [1, 4],
                'type': 'connector',
                'module_path': 'opsdroid-modules.connector.shell'
            }, opsdroid=opsdroid)

            with amock.patch('asyncio.sleep') as mocksleep_list:
                message = events.Message("hi", "user", "default", mock_connector_list)
                with self.assertRaises(TypeError):
                    await message.respond("Hello there")

                self.assertTrue(mocksleep_list.called)

    async def test_typing_delay(self):
        with OpsDroid() as opsdroid:
            mock_connector = Connector({
                'name': 'shell',
                'typing-delay': 0.3,
                'type': 'connector',
                'module_path': 'opsdroid-modules.connector.shell'
            }, opsdroid=opsdroid)
            with amock.patch(
                    'opsdroid.events.Message._typing_delay') as logmock:
                with amock.patch('asyncio.sleep') as mocksleep:
                    message = events.Message("hi", "user", "default", mock_connector)
                    with self.assertRaises(TypeError):
                        await message.respond("Hello there")

                    self.assertTrue(logmock.called)
                    self.assertTrue(mocksleep.called)

            # Test thinking-delay with a list

            mock_connector_list = Connector({
                'name': 'shell',
                'typing-delay': [1, 4],
                'type': 'connector',
                'module_path': 'opsdroid-modules.connector.shell'
            }, opsdroid=opsdroid)

            with amock.patch('asyncio.sleep') as mocksleep_list:
                message = events.Message("hi", "user", "default", mock_connector_list)
                with self.assertRaises(TypeError):
                    await message.respond("Hello there")

                self.assertTrue(mocksleep_list.called)

    async def test_typing_sleep(self):
        with OpsDroid() as opsdroid:
            mock_connector = Connector({
                'name': 'shell',
                'typing-delay': 6,
                'type': 'connector',
                'module_path': 'opsdroid-modules.connector.shell'
            }, opsdroid=opsdroid)
            with amock.patch('asyncio.sleep') as mocksleep:
                message = events.Message("hi", "user", "default", mock_connector)
                with self.assertRaises(TypeError):
                    await message.respond("Hello there")

                self.assertTrue(mocksleep.called)

    async def test_react(self):
        with OpsDroid() as opsdroid:
            mock_connector = Connector({
                'name': 'shell',
                'thinking-delay': 2,
                'type': 'connector',
            }, opsdroid=opsdroid)
            with amock.patch('asyncio.sleep') as mocksleep:
                message = events.Message("Hello world", "user", "default", mock_connector)
                with self.assertRaises(TypeError):
                    await message.respond(events.Reaction("emoji"))
                self.assertTrue(mocksleep.called)


class TestFile(asynctest.TestCase):
    """Test the opsdroid file class"""

    async def setup(self):
        configure_lang({})

    async def test_file(self):
        opsdroid = amock.CoroutineMock()
        mock_connector = Connector({}, opsdroid=opsdroid)
        event = events.File(
            bytes("some file contents", "utf-8"),
            user="user",
            target="default",
            connector=mock_connector)

        self.assertEqual(event.user, "user")
        self.assertEqual(event.target, "default")
        self.assertEqual(event.file_bytes.decode(), "some file contents")

    def test_error_on_construct(self):
        with self.assertRaises(ValueError):
            events.File()

        with self.assertRaises(ValueError):
            events.File(b"a", "https://localhost")

    def test_file_bytes(self):
        f = events.File(url="http://spam.eggs/monty.jpg")
        with mock.patch("urllib.request.urlopen") as patch_urlopen:
            response = mock.Mock()
            response.__enter__ = mock.Mock(return_value=response)
            response.__exit__ = mock.Mock(return_value=False)
            response.read = mock.Mock()
            response.read.return_value = b"bob"
            patch_urlopen.return_value = response

            assert f.file_bytes == b"bob"
            assert patch_urlopen.call_count == 1

            # Now test we don't re-download the url
            assert f.file_bytes == b"bob"
            assert patch_urlopen.call_count == 1


class TestImage(asynctest.TestCase):
    """Test the opsdroid image class"""

    async def setup(self):
        configure_lang({})

    async def test_image(self):
        opsdroid = amock.CoroutineMock()
        mock_connector = Connector({}, opsdroid=opsdroid)
        event = events.Image(
            bytes("some image contents", "utf-8"),
            user="user",
            target="default",
            connector=mock_connector)

        self.assertEqual(event.user, "user")
        self.assertEqual(event.target, "default")
        self.assertEqual(event.image_bytes.decode(), "some image contents")
