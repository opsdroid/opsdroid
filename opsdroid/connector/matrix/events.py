"""Matrix specific events."""

from opsdroid.events import Event


__all__ = [
    "MatrixRoomAvatar",
    "MatrixHistoryVisibility",
    "MatrixJoinRules",
    "MatrixPowerLevels",
    "MatrixStateEvent",
]


class MatrixStateEvent(Event):
    """A Generic matrix state event."""

    def __init__(self, key, content, *args, state_key=None, **kwargs):  # noqa: D107
        super().__init__(*args, **kwargs)
        self.key = key
        self.content = content
        self.state_key = state_key

    def __repr__(self):
        """Pretty representation of state events."""
        return f"<MatrixStateEvent(room_id={self.target}, key={self.key}, content={self.content})>"


class MatrixPowerLevels(MatrixStateEvent):
    """Send power levels."""

    def __init__(self, power_levels, *args, **kwargs):  # noqa: D107
        key = "m.room.power_levels"
        super().__init__(key, power_levels, *args, **kwargs)


class MatrixJoinRules(MatrixStateEvent):
    """The room's join rules."""

    def __init__(self, join_rule, *args, **kwargs):  # noqa: D107
        key = "m.room.join_rules"
        content = {"join_rule": join_rule}
        super().__init__(key, content, *args, **kwargs)


class MatrixHistoryVisibility(MatrixStateEvent):
    """The room's history visibility."""

    def __init__(self, history_visibility, *args, **kwargs):  # noqa: D107
        key = "m.room.history_visibility"
        content = {"history_visibility": history_visibility}
        super().__init__(key, content, *args, **kwargs)


class MatrixRoomAvatar(MatrixStateEvent):
    """The room's avatar."""

    def __init__(self, url, *args, **kwargs):  # noqa: D107
        key = "m.room.avatar"
        content = {"url": url}
        super().__init__(key, content, *args, **kwargs)
