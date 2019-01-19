"""Support for deprecated opsdroid.message.Message"""

from warnings import warn

from opsdroid.events import Message as NewMessage


warn("opsdroid.message.Message is deprecated. "
     "Please use opsdroid.events.Message instead.",
     DeprecationWarning)


def Message(text, user, room, connector, raw_message=None):
    return NewMessage(user, room, connector, text, raw_message)
