"""Class to encapsulate a message."""

from copy import copy


class Message:
    # pylint: disable=too-few-public-methods
    """A message object."""

    def __init__(self, text, user, room, connector):
        """Create object with minimum properties."""
        self.text = text
        self.user = user
        self.room = room
        self.connector = connector
        self.regex = None

    async def respond(self, text):
        """Respond to this message using the connector it was created by."""
        response = copy(self)
        response.text = text
        await self.connector.respond(response)
