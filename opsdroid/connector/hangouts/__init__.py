"""A connector for Slack."""
import logging

import aiohttp
import hangups

from opsdroid.connector import Connector


_LOGGER = logging.getLogger(__name__)


class ConnectorHangouts(Connector):
    """A connector for Hangups."""

    def __init__(self, config):
        """Create the connector."""
        super().__init__(config)
        _LOGGER.debug("Starting Hangups connector")
        self.name = "hangups"
        self.config = config
        self.listening = True
        self.opsdroid = None
        self.args = None
        self.cookies = hangups.auth.get_auth_stdin('')
        self.client = hangups.Client(self.cookies)

    async def connect(self, opsdroid=None):
        """Connect to the chat service."""
        if opsdroid is not None:
            self.opsdroid = opsdroid

        _LOGGER.info("Connecting to Hangouts")

        try:
            await self.client.connect()
        except aiohttp.ClientOSError as error:
            _LOGGER.error(error)
            _LOGGER.error("Failed to connect to Hangouts")

    async def listen(self, opsdroid):
        """Listen for and parse new messages."""
        pass

    async def respond(self, opsdroid):
        """Get the next message from the websocket."""
        pass

    async def disconnect(self, opsdroid):
        """disconnect from chat service"""
        self.client.disconnect()
