"""Tests for the shell connector class."""
import os
import io
import contextlib
import asyncio
import unittest
import unittest.mock as mock
import asynctest
import asynctest.mock as amock

from opsdroid.core import OpsDroid
from opsdroid.connector.shell import ConnectorShell
from opsdroid.message import Message
from opsdroid.__main__ import configure_lang


class TestConnectorShell(unittest.TestCase):
    """Test the opsdroid shell connector class."""

    def setUp(self):
        self.connector = ConnectorShell({
            'name': 'shell',
            'bot-name': 'opsdroid-test'
        })
        self.loop = asyncio.new_event_loop()
        configure_lang({})
        os.environ["USERNAME"] = "opsdroid"

    def test_init(self):
        """Test that the connector is initialised properly."""
        self.assertEqual(self.connector.user, 'opsdroid')
        self.assertEqual(len(self.connector.config), 2)
        self.assertEqual("shell", self.connector.name)
        self.assertEqual('opsdroid-test', self.connector.bot_name)

    def test_clear_prompt(self):
        self.connector.prompt_length = 1

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            self.connector.clear_prompt()
            prompt = f.getvalue()
            self.assertEqual(prompt, '\r \r')

    def test_draw_prompt(self):
        self.assertEqual(self.connector.prompt_length, None)

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            self.connector.prompt_length = 1
            self.connector.draw_prompt()
            prompt = f.getvalue()
            self.assertEqual(prompt, 'opsdroid-test> ')
        self.connector.draw_prompt()
        self.assertEqual(self.connector.prompt_length, 15)


class TestConnectorShellAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid shell connector class."""

    def setUp(self):
        os.environ["LOGNAME"] = "opsdroid"
        self.connector = ConnectorShell({
                'name': 'shell',
                'bot-name': 'opsdroid'
            })

    async def test_read_stdin(self):
        with amock.patch(
                'opsdroid.connector.shell.ConnectorShell.read_stdin') \
                as mocked_read_stdin:
            await self.connector.read_stdin()
            self.assertTrue(mocked_read_stdin.called)

    async def test_connect(self):
        with OpsDroid() as opsdroid:
            await self.connector.connect(opsdroid)

            self.assertTrue(self.connector.connect)

    @amock.patch('opsdroid.connector.shell.ConnectorShell.read_stdin')
    async def test_async_input(self, mocked_read):
        mocked_read.readline.return_value.side_effect = 'hi'
        with contextlib.suppress(AttributeError, TypeError):
            await self.connector.async_input()
            self.assertEqual(mocked_read, 'hi')

    async def test_parse_message(self):

        with OpsDroid() as opsdroid,\
                amock.patch('opsdroid.core.OpsDroid.parse') as mocked_parse, \
                amock.patch(
                    'opsdroid.connector.shell.ConnectorShell.async_input') \
                as mocked_input:
            mocked_input = amock.CoroutineMock(return_value='')
            await self.connector._parse_message(opsdroid)
            self.assertTrue(mocked_parse.called)
            self.assertTrue(mocked_input)

    async def test_listen_fail(self):
        with contextlib.suppress(io.UnsupportedOperation):
            self.connector.side_effect = Exception()
            await self.connector.listen(amock.CoroutineMock())

    async def test_listen_(self):
        self.connector.listening = False
        with OpsDroid() as opsdroid, \
            amock.patch(
                'opsdroid.connector.shell.ConnectorShell._parse_message') \
                as mocked_listen:
            await self.connector.listen(opsdroid)
            self.assertFalse(mocked_listen.called)

    async def test_respond(self):
        message = Message(text="Hi",
                          user="opsdroid",
                          room="test",
                          connector=self.connector)
        self.connector.prompt_length = 1

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            await self.connector.respond(message)
            prompt = f.getvalue()
            self.assertEqual(prompt.strip(), 'Hi\nopsdroid>')
