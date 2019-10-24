from opsdroid.events import Event


class FeedItemEvent(Event):
    """A feed item has been created."""

    def __init__(self, item, *args, **kwargs):
        """Create object with minimum properties."""
        super().__init__(*args, **kwargs)
        self.item = item

    def __repr__(self):
        return f"<FeedItemEvent()>"

    async def respond(self, event):
        raise NotImplementedError("You cannot respond to a feed item.")
