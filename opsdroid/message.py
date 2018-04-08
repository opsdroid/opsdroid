"""Class to encapsulate a message."""

from datetime import datetime
from copy import copy
import asyncio
from random import randrange

from opsdroid.helper import get_opsdroid


class Message:
    # pylint: disable=too-few-public-methods
    """A message object."""

    def __init__(self, text, user, room, connector, raw_message=None):
        """Create object with minimum properties."""
        self.created = datetime.now()
        self.text = text
        self.user = user
        self.room = room
        self.connector = connector
        self.raw_message = raw_message
        self.regex = None
        self.responded_to = False

    async def _thinking_delay(self):
        """Make opsdroid wait x-seconds before responding."""
        seconds = self.connector.configuration.get('thinking-delay', 0)

        if isinstance(seconds, list):
            seconds = randrange(seconds[0], seconds[1])

        await asyncio.sleep(seconds)

    async def _typing_delay(self, text):
        """Simulate typing, takes an int or float to delay reply."""
        seconds = self.connector.configuration.get('typing-delay', 0)
        char_count = len(text)

        if isinstance(seconds, list):
            seconds = randrange(seconds[0], seconds[1])

        await asyncio.sleep(char_count*seconds)

    async def respond(self, text, room=None):
        """Respond to this message using the connector it was created by."""
        opsdroid = get_opsdroid()
        response = copy(self)
        response.text = text

        if 'thinking-delay' in self.connector.configuration or \
           'typing-delay' in self.connector.configuration:
            await self._thinking_delay()
            await self._typing_delay(response.text)

        await self.connector.respond(response, room)
        if not self.responded_to:
            now = datetime.now()
            opsdroid.stats["total_responses"] = \
                opsdroid.stats["total_responses"] + 1
            opsdroid.stats["total_response_time"] = \
                opsdroid.stats["total_response_time"] + \
                (now - self.created).total_seconds()
            self.responded_to = True

    async def react(self, emoji):
        """React to this message using the connector it was created by."""
        if 'thinking-delay' in self.connector.configuration:
            await self._thinking_delay()
        return await self.connector.react(self, emoji)
