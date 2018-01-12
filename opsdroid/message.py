"""Class to encapsulate a message."""

from datetime import datetime
from copy import copy
import asyncio
from random import randrange

from opsdroid.helper import get_opsdroid


class Message:
    # pylint: disable=too-few-public-methods
    """A message object."""

    def __init__(self, text, user, room, connector):
        """Create object with minimum properties."""
        self.created = datetime.now()
        self.text = text
        self.user = user
        self.room = room
        self.connector = connector
        self.regex = None
        self.responded_to = False

    async def _thinking_delay(self, seconds=0):
        """Make opsdroid wait x-seconds before responding."""
        seconds = self.connector.configuration.get('thinking-delay', 0)

        if isinstance(seconds, list):
            seconds = randrange(seconds[0], seconds[1])

        await asyncio.sleep(seconds)

    async def _typing_delay(self, text):
        """Simulate typing, default is set to 6 characters per second."""
        seconds = self.connector.configuration.get('typing-delay', 1)

        char_count = len(text)
        await asyncio.sleep(char_count//seconds)

    async def respond(self, text):
        """Respond to this message using the connector it was created by."""
        opsdroid = get_opsdroid()
        response = copy(self)
        response.text = text

        await self._thinking_delay()
        await self._typing_delay(response.text,)
        print(self.connector.configuration)
        await self.connector.respond(response)
        if not self.responded_to:
            now = datetime.now()
            opsdroid.stats["total_responses"] = \
                opsdroid.stats["total_responses"] + 1
            opsdroid.stats["total_response_time"] = \
                opsdroid.stats["total_response_time"] + \
                (now - self.created).total_seconds()
            self.responded_to = True
