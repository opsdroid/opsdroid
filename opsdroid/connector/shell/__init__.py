"""A connector to send messages using the command line."""
import logging
import os
import sys
import asyncio
from asyncio.streams import StreamWriter, FlowControlMixin

from opsdroid.connector import Connector
from opsdroid.message import Message

_LOGGER = logging.getLogger(__name__)


class ConnectorShell(Connector):
    """A connector to send messages using the command line."""

    def __init__(self, config):
        """Create the connector."""
        _LOGGER.debug(_("Loaded shell connector"))
        super().__init__(config)
        self.name = "shell"
        self.config = config
        self.bot_name = config.get("bot-name", "opsdroid")
        self.prompt_length = None
        self.listening = True
        self.reader = None
        self.writer = None

        for name in ('LOGNAME', 'USER', 'LNAME', 'USERNAME'):
            user = os.environ.get(name)
            if user:
                self.user = user

    async def stdio(self):
        """Create Standard I/O logic."""
        loop = asyncio.get_event_loop()

        self.reader = asyncio.StreamReader()
        reader_protocol = asyncio.StreamReaderProtocol(self.reader)

        writer_transport, writer_protocol = await loop.connect_write_pipe(
            FlowControlMixin, os.fdopen(0, 'wb'))

        self.writer = StreamWriter(
            writer_transport, writer_protocol, None, loop)

        await loop.connect_read_pipe(lambda: reader_protocol, sys.stdin)

        return self.reader, self.writer

    async def async_input(self, message):
        """User input."""
        if isinstance(message, str):
            message = message.encode('utf8')

        if (self.reader, self.writer) == (None, None):
            self.reader, self.writer = await self.stdio()

        self.writer.write(message)
        await self.writer.drain()

        line = await self.reader.readline()
        return line.decode('utf8').replace('\r', '').replace('\n', '')

    def draw_prompt(self):
        """Draw the user input prompt."""
        prompt = self.bot_name + '> '
        self.prompt_length = len(prompt)
        print(prompt, end="", flush=True)

    def clear_prompt(self):
        """Clear the prompt."""
        print("\r" + (" " * self.prompt_length) + "\r", end="", flush=True)

    async def connect(self, opsdroid):
        """Connect to the shell.

        There is nothing to do here since stdin is already available.

        """
        pass

    async def listen(self, opsdroid):
        """Listen for and parse new user input.

        Args:
            opsdroid (Opsdroid): An instance of opsdroid core.

        """
        _LOGGER.debug(_("Connecting to shell"))
        while self.listening:
            self.draw_prompt()
            user_input = await self.async_input('')
            message = Message(user_input, self.user, None, self)
            await opsdroid.parse(message)

    async def respond(self, message, room=None):
        """Respond with a message.

        Args:
            message (object): An instance of Message
            room (string, optional): Name of the room to respond to.

        """
        _LOGGER.debug(_("Responding with: %s"), message.text)
        self.clear_prompt()
        print(message.text)
        self.draw_prompt()
