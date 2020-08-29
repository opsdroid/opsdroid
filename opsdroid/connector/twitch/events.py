"""Events for Twitch Connector."""
import logging

from opsdroid import events

_LOGGER = logging.getLogger(__name__)


class UserFollowed(events.Event):
    """Event class to trigger when a user follows the streamer."""

    def __init__(self, follower, followed_at, *args, **kwargs):
        """Follower username of the follower, followed_at is the timestamp of the following."""
        super().__init__(*args, **kwargs)
        self.follower = follower
        self.followed_at = followed_at


class StreamStarted(events.Event):
    """Event class that triggers when streamer started broadcasting."""

    def __init__(self, title, viewers, started_at, *args, **kwargs):
        """Event that is triggered when a streamer starts broadcasting.

        This event is triggered after 2 minutes of starting the broascast and
        contains a few attributes that you can access.

        ``title`` your broadcast title
        ``viewers`` total number of viewers that your channel has
        ``started_at`` timestamp when you went live

        """
        super().__init__(*args, **kwargs)
        self.title = title
        self.viewers = viewers
        self.started_at = started_at


class StreamEnded(events.Event):
    """Event class that triggers when streamer stoppped broadcasting."""


class CreateClip(events.Event):
    """Event class that creates a clip once triggered."""

    def __init__(self, id, *args, **kwargs):
        """Id is your streamer id."""
        super().__init__(*args, **kwargs)
        self.id = id


class UpdateTitle(events.Event):
    """Event class that updates channel title."""

    def __init__(self, status, *args, **kwargs):
        """Status is the new title for your channel."""
        super().__init__(*args, **kwargs)
        self.status = status


class UserSubscribed(events.Event):
    """Event class that triggers whenever a user subscribes to the channel."""

    def __init__(self, user, message, *args, **kwargs):
        """User is the username of the subscriber, message is the sub message, can be None."""
        super().__init__(*args, **kwargs)
        self.user = user
        self.message = message


class UserGiftedSubscription(events.Event):
    """Event class that triggers when a user gifts a subscription to someone."""

    def __init__(self, gifter_name, gifted_named, *args, **kwargs):
        """Gifter_name is the sub that gifted a sub, gifted name is the gifted viewer."""
        super().__init__(*args, **kwargs)
        self.gifter_name = gifter_name
        self.gifted_name = gifted_named
