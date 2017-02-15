"""Class to encapsulate a message."""

from datetime import datetime

from copy import copy

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

    async def respond(self, text):
        """Respond to this message using the connector it was created by."""
        opsdroid = get_opsdroid()
        response = copy(self)
        response.text = text
        await self.connector.respond(response)
        if not self.responded_to:
            now = datetime.now()
            opsdroid.stats["total_responses"] = \
                opsdroid.stats["total_responses"] + 1
            opsdroid.stats["total_response_time"] = \
                opsdroid.stats["total_response_time"] + \
                (now - self.created).total_seconds()
            self.responded_to = True
