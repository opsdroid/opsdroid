"""A connector to send messages using the command line."""
import logging
import os
import sys
import platform
import asyncio

from opsdroid.connector import Connector, register_event
from opsdroid.events import Message

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = {"bot-name": str}


class ConnectorShell(Connector):
    """A connector to send messages using the command line."""

    def __init__(self, config, opsdroid=None):
        """Create the connector."""
        _LOGGER.debug(_("Loaded shell Connector."))
        super().__init__(config, opsdroid=opsdroid)
        self.name = "shell"
        self.config = config
        self.bot_name = config.get("bot-name", "opsdroid")
        self.prompt_length = None
        self.listening = True
        self.reader = None
        self._closing = asyncio.Event()
        self.loop = asyncio.get_event_loop()

        for name in ("LOGNAME", "USER", "LNAME", "USERNAME"):
            user = os.environ.get(name)
            if user:
                self.user = user

    @property
    def is_listening(self):
        """Get listening status."""
        return self.listening

    @is_listening.setter
    def is_listening(self, val):
        """Set listening status."""
        self.listening = val

    async def read_stdin(self):
        """Create a stream reader to read stdin asynchronously.

        Returns:
            class: asyncio.streams.StreamReader

        """
        self.reader = asyncio.StreamReader(loop=self.loop)
        reader_protocol = asyncio.StreamReaderProtocol(self.reader)

        await self.loop.connect_read_pipe(lambda: reader_protocol, sys.stdin)

        return self.reader

    async def async_input(self):
        """Read user input asynchronously from stdin.

        Returns:
            string: A decoded string from user input.

        """
        if not self.reader:
            self.reader = await self.read_stdin()
        line = await self.reader.readline()

        return line.decode("utf8").replace("\r", "").replace("\n", "")

    def draw_prompt(self):
        """Draw the user input prompt."""
        prompt = self.bot_name + "> "
        self.prompt_length = len(prompt)
        print(prompt, end="", flush=True)

    def clear_prompt(self):
        """Clear the prompt."""
        print("\r" + (" " * self.prompt_length) + "\r", end="", flush=True)

    async def parseloop(self):
        """Parseloop moved out for testing."""
        self.draw_prompt()
        user_input = await self.async_input()
        message = Message(text=user_input, user=self.user, target=None, connector=self)
        await self.opsdroid.parse(message)

    async def _parse_message(self):
        """Parse user input."""
        while self.is_listening:
            await self.parseloop()

    async def connect(self):
        """Connect to the shell.

        There is nothing to do here since stdin is already available.

        Since this is the first method called when opsdroid starts, a logging
        message is shown if the user is using windows.

        """
        if platform.system() == "Windows":
            _LOGGER.warning(
                "The shell connector does not work on windows. Please install the Opsdroid Desktop App."
            )
        pass

    async def listen(self):
        """Listen for and parse new user input."""
        _LOGGER.debug(_("Connecting to shell."))
        message_processor = self.loop.create_task(self._parse_message())
        await self._closing.wait()
        message_processor.cancel()

    @register_event(Message)
    async def respond(self, message):
        """Respond with a message.

        Args:
            message (object): An instance of Message

        """
        _LOGGER.debug(_("Responding with: %s."), message.text)
        self.clear_prompt()
        print(message.text)

    async def disconnect(self):
        """Disconnects the connector."""
        self._closing.set()
