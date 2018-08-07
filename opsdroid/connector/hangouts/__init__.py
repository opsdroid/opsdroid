"""A connector for Slack."""
import logging
import asyncio
import json
import re
import argparse
import os
import appdirs

import aiohttp
import hangups

from opsdroid.connector import Connector
from opsdroid.message import Message


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
        # self.cookies = hangups.auth.get_auth_stdin('/home/gabeduke/.local/share/hangupsbot/cookies.json')
        self.client = hangups.Client(self.cookies)

    async def connect(self, opsdroid=None):
        """Connect to the chat service."""
        if opsdroid is not None:
            self.opsdroid = opsdroid

        _LOGGER.info("Connecting to Hangouts")

        try:
            connection = await self.client.connect()
        except aiohttp.ClientOSError as error:
            _LOGGER.error(error)
            _LOGGER.error("Failed to connect to Hangouts")

    async def listen(self, opsdroid):
        _LOGGER.info('loading conversation list...')
        user_list, conv_list = (
            await hangups.build_user_conversation_list(self.client)
        )

    async def respond(self, opsdroid):
        pass

    async def disconnect(self, opsdroid):
        self.client.disconnect()