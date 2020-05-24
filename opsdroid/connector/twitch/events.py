import logging

from opsdroid import events

_LOGGER = logging.getLogger(__name__)


class DeleteMessage(events.Event):
    """Event class to trigger specific message deletion."""
    def __init__(self, id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = id


class BanUser(events.Event):
    """Event class to ban a user from the channel."""
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user


class UserFollowed(events.Event):
    """Event class to trigger when a user follows the streamer."""
    def __init__(self, follower, followed_at, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.follower = follower
        self.followed_at = followed_at


class UserSubscribed(events.Event):
    """Event class to trigger when a user subscribes to a channel."""
    def __init__(self, user, subscribed_at, message, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.subscribed_at = subscribed_at
        self.message = message


class StreamStarted(events.Event):
    """Event class that triggers when streamer started broadcasting."""
    def __init__(self, title, viewers, started_at, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title = title
        self.viewers = viewers
        self.started_at = started_at


class StreamEnded(events.Event):
    """Event class that triggers when streamer stoppped broadcasting."""


class CreateClip(events.Event):
    def __init__(self, id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = id


class UpdateTitle(events.Event):
    def __init__(self, status, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = status