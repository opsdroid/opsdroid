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
    """Event class that creates a clip once triggered."""
    def __init__(self, id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = id


class UpdateTitle(events.Event):
    """Event class that updates channel title."""
    def __init__(self, status, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = status


class UserSubscribed(events.Event):
    """Event class that triggers whenever a user subscribes to the channel."""
    def __init__(self, username, message, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.username = username
        self.message = message


class UserGiftedSubscription(events.Event):
    """Event class that triggers when a user gifts a subscription to someone."""
    def __init__(self, gifter_name, gifted_named, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gifter_name = gifter_name
        self.gifted_name = gifted_named
