from opsdroid.events import Event


class FeedItemEvent(Event):
    """A feed item has been created."""

    def __repr__(self):
        return f"<FeedItemEvent()>"
