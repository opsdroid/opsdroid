"""Tests for the shell connector class."""
import os
import io
import contextlib
import asyncio
import unittest
import asynctest
import asynctest.mock as amock

from opsdroid.core import OpsDroid
from opsdroid.connector.shell import ConnectorShell
from opsdroid.message import Message
from opsdroid.cli.start import configure_lang


class TestConnectorShell(unittest.TestCase):
    """Test the opsdroid shell connector class."""

    def setUp(self):
        self.connector = ConnectorShell({"name": "shell", "bot-name": "opsdroid-test"})
        self.loop = asyncio.new_event_loop()
        configure_lang({})
        os.environ["USERNAME"] = "opsdroid"

    def test_init(self):
        """Test that the connector is initialised properly."""
        self.assertEqual(self.connector.user, "opsdroid")
        self.assertEqual(len(self.connector.config), 2)
        self.assertEqual("shell", self.connector.name)
        self.assertEqual("opsdroid-test", self.connector.bot_name)

    def test_is_listening(self):
        self.assertEqual(self.connector.listening, self.connector.is_listening)

    def test_is_listening_setter(self):
        self.assertEqual(self.connector.listening, self.connector.is_listening)
        self.connector.is_listening = False
        self.assertFalse(self.connector.listening)

    def test_draw_prompt(self):
        self.assertEqual(self.connector.prompt_length, None)

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            self.connector.prompt_length = 1
            self.connector.draw_prompt()
            prompt = f.getvalue()
            self.assertEqual(prompt, "opsdroid-test> ")
        self.connector.draw_prompt()
        self.assertEqual(self.connector.prompt_length, 15)

    def test_clear_prompt(self):
        self.connector.prompt_length = 1

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            self.connector.clear_prompt()
            prompt = f.getvalue()
            self.assertEqual(prompt, "\r \r")


class TestConnectorShellAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid shell connector class."""

    def setUp(self):
        os.environ["LOGNAME"] = "opsdroid"
        self.connector = ConnectorShell({"name": "shell", "bot-name": "opsdroid"})

    async def test_read_stdin(self):
        with amock.patch(
            "opsdroid.connector.shell.ConnectorShell.read_stdin"
        ) as mocked_read_stdin:
            await self.connector.read_stdin()
            self.assertTrue(mocked_read_stdin.called)

        if os.name == "nt":
            with amock.patch("asyncio.events.AbstractEventLoop.connect_read_pipe"):
                with contextlib.suppress(NotImplementedError):
                    await self.connector.read_stdin()
        else:
            self.connector.loop.connect_read_pipe = amock.CoroutineMock()
            self.connector.reader = None
            self.assertIsNone(self.connector.reader)
            result = await self.connector.read_stdin()
            self.assertEqual(result, self.connector.reader)

    async def test_connect(self):
        connector = ConnectorShell({}, opsdroid=OpsDroid())
        await connector.connect()
        self.assertTrue(connector.connect)

        with amock.patch("platform.system", amock.MagicMock(return_value="Windows")):
            await connector.connect()
            self.assertTrue(connector.connect)

    @amock.patch("opsdroid.connector.shell.ConnectorShell.read_stdin")
    async def test_async_input(self, mocked_read):
        mocked_read.readline.return_value.side_effect = "hi"
        with contextlib.suppress(AttributeError, TypeError):
            await self.connector.async_input()
            self.assertEqual(mocked_read, "hi")

        connector = ConnectorShell({}, opsdroid=OpsDroid())
        f = asyncio.Future()
        f.set_result(b"hi\n")

        with asynctest.patch("asyncio.streams.StreamReader.readline") as mocked_line:
            mocked_line.return_value = f
            connector.reader = asyncio.streams.StreamReader
            returned = await connector.async_input()
            self.assertEqual(returned, "hi")

    async def test_parse_message(self):
        connector = ConnectorShell({}, opsdroid=OpsDroid())

        with amock.patch(
            "opsdroid.connector.shell.ConnectorShell.parseloop"
        ) as mockedloop:
            self.assertTrue(connector.listening)
            connector.listening = True
            with amock.patch(
                "opsdroid.connector.shell.ConnectorShell.is_listening",
                new_callable=amock.PropertyMock,
                side_effect=[True, False],
            ):
                await connector._parse_message()
                mockedloop.assert_called()

    async def test_parseloop(self):
        connector = ConnectorShell({}, opsdroid=OpsDroid())

        connector.draw_prompt = amock.CoroutineMock()
        connector.draw_prompt.return_value = "opsdroid> "
        connector.async_input = amock.CoroutineMock()
        connector.async_input.return_value = "hello"

        connector.opsdroid = amock.CoroutineMock()
        connector.opsdroid.parse = amock.CoroutineMock()

        await connector.parseloop()
        self.assertTrue(connector.opsdroid.parse.called)

    async def test_listen(self):
        connector = ConnectorShell({}, opsdroid=OpsDroid())
        connector.listening = False
        with amock.patch("asyncio.events.AbstractEventLoop.create_task"), amock.patch(
            "asyncio.locks.Event.wait"
        ):
            await connector.listen()

    async def test_respond(self):
        message = Message(
            text="Hi", user="opsdroid", room="test", connector=self.connector
        )
        self.connector.prompt_length = 1

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            await self.connector.respond(message)
            prompt = f.getvalue()
            self.assertEqual(prompt.strip(), "Hi")

    async def test_disconnect(self):
        connector = ConnectorShell({}, opsdroid=OpsDroid())
        await connector.disconnect()
        self.assertEqual(connector._closing.set(), None)
