"""Events for the Telegram Connector."""
from opsdroid import events


class Poll(events.Event):
    """Event class that triggers when a poll is sent."""

    def __init__(self, poll, *args, **kwargs):
        """Add the poll parameter to the event."""
        super().__init__(*args, **kwargs)
        self.poll = poll


class Contact(events.Event):
    """Event class that triggers when a contact is sent."""

    def __init__(self, contact, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.contact = contact


class Location(events.Event):
    def __init__(self, location, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.location = location
