"""Support for deprecated opsdroid.message.Message."""

from warnings import warn

from opsdroid.events import Message as NewMessage


warn("opsdroid.message.Message is deprecated. "
     "Please use opsdroid.events.Message instead.",
     DeprecationWarning)


# pylint: disable=C0103
def Message(text, user, room, connector, raw_message=None):
    """
    Stand-in function for the deprecated opsdroid.message.Message object.

    Returns a new opsdroid.events.Message object using the same arguments.
    """
    return NewMessage(text, user, room, connector, raw_event=raw_message)

    @property
    def room(self):
        warn(
            "Message.room is deprecated. Use "
            "Message.target instead.",
            DeprecationWarning)

        return self.target

    @room.setter
    def room(self, value):
        warn(
            "Message.room is deprecated. Use "
            "Message.target instead.",
            DeprecationWarning)

        self.target = value

    @property
    def raw_message(self):
        warn(
            "Message.raw_message is deprecated. Use "
            "Message.raw_event instead.",
            DeprecationWarning)

        return self.raw_event

    @raw_message.setter
    def raw_message(self, value):
        warn(
            "Message.raw_message is deprecated. Use "
            "Message.raw_event instead.",
            DeprecationWarning)

        self.raw_event = value
