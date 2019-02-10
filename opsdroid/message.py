"""Support for deprecated opsdroid.message.Message."""

from warnings import warn

from opsdroid.events import Message as NewMessage


warn("opsdroid.message.Message is deprecated. "
     "Please use opsdroid.events.Message instead.",
     DeprecationWarning)


# pylint: disable=C0103
def Message(text, user, room, connector, raw_event=None):
    """
    Stand-in function for the deprecated opsdroid.message.Message object.

    Returns a new opsdroid.events.Message object using the same arguments.
    """
    return NewMessage(text, user, room, connector, raw_event=raw_event)
