"""Class to encapsulate a message."""

from datetime import datetime
from copy import copy
import asyncio
from random import randrange

from opsdroid.helper import get_opsdroid

"""
Working checklist
# Message
"""

class Message:
    # pylint: disable=too-few-public-methods
    """A message object.
    
    Stores messages in format that allows OpsDroid to respond or react with
    delays for thinking and typing as defined in configuration YAML file.
    
    Args:
        text: String text of message
        user: String name of user sending message
        room: String name of the room or chat channel in which message was sent
        connector: Connector object used to interact with given chat service
        raw_message: Raw message as provided by chat service. None by default
    
    Attributes:
        created: Local date and time that message object was created
        text: Text of message as string
        user: String name of user sending message
        room: String name of the room or chat channel in which message was sent
        connector: Connector object used to interact with given chat service
        raw_message: Raw message as provided by chat service, e.g. string or dictionary
        regex: A re match object for the regular expression message was matched against
        responded_to: Boolean initialized as False. True if message has been responded to
    """

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
        """Make opsdroid wait x-seconds before responding.
        
        Number of seconds is defined in YAML config. file, accessed via connector.
        """
        seconds = self.connector.configuration.get('thinking-delay', 0)

        if isinstance(seconds, list):
            seconds = randrange(seconds[0], seconds[1])

        await asyncio.sleep(seconds)

    async def _typing_delay(self, text):
        """Delays reply to simulate typing.
        
        Seconds to delay equals number of characters in response multiplied by
        number of seconds defined in YAML config. file, accessed via connector.
        """
        seconds = self.connector.configuration.get('typing-delay', 0)
        char_count = len(text)

        if isinstance(seconds, list):
            seconds = randrange(seconds[0], seconds[1])

        await asyncio.sleep(char_count*seconds)

    async def respond(self, text, room=None):
        """Respond to this message using the connector it was created by.
        
        Creates copy of this message with updated text as response.
        Delays message with _thinking_delay, _typing_delay if present in config. file.
        Updates responded_to attribute to True if message not already responded to.
        Logs response and response time in OpsDroid object stats
        """
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
        """React to this message with emoji using the specified connector.
        
        Delays message with _thinking_delay if present in config. file.
        
        Args:
            emoji: Sting name of emoji with which OpsDroid will react
        
        Returns:
            bool: True for message successfully sent. False otherwise.
            
        """
        if 'thinking-delay' in self.connector.configuration:
            await self._thinking_delay()
        return await self.connector.react(self, emoji)