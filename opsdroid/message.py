"""Support for deprecated opsdroid.message.Message."""

import warnings

from opsdroid.events import Message as NewMessage


warnings.warn(
    "opsdroid.message.Message is deprecated. "
    "Please use opsdroid.events.Message instead.",
    DeprecationWarning,
)


# pylint: disable=C0103
class Message(NewMessage):
    """A message object.

    Deprecated. Use ``opsdroid.events.Message`` instead.
    """

    # Skip registering this class with Event
    _no_register = True

    def __init__(self, text, user, room, connector, raw_message=None):  # noqa: D401
        """Deprecated opsdroid.message.Message object."""
        super().__init__(
            text=text,
            user=user,
            target=room,
            connector=connector,
            raw_event=raw_message,
        )

    @property
    def room(self):  # noqa: D401
        """The room the message was sent into."""
        warnings.warn(
            "Message.room is deprecated. Use " "Message.target instead.",
            DeprecationWarning,
        )

        return self.target

    @room.setter
    def room(self, value):
        warnings.warn(
            "Message.room is deprecated. Use " "Message.target instead.",
            DeprecationWarning,
        )

        self.target = value

    @property
    def raw_message(self):  # noqa: D401
        """The raw contents of the message."""
        warnings.warn(
            "Message.raw_message is deprecated. Use " "Message.raw_event instead.",
            DeprecationWarning,
        )

        return self.raw_event

    @raw_message.setter
    def raw_message(self, value):
        warnings.warn(
            "Message.raw_message is deprecated. Use " "Message.raw_event instead.",
            DeprecationWarning,
        )

        self.raw_event = value
