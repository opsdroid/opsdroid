"""Event objects specific to the rss connector."""

from opsdroid.events import Event


class FeedItemEvent(Event):
    """A feed item has been created."""

    def __init__(self, item, *args, **kwargs):
        """Create object with minimum properties."""
        super().__init__(*args, **kwargs)
        self.item = item

    def __repr__(self):
        """Override Event's representation so you can see the text when you print it."""
        return f"<FeedItemEvent()>"

    async def respond(self, event):
        """Disable the respond method as it does not make sense for feed items."""
        raise NotImplementedError("You cannot respond to a feed item.")
