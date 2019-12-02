"""Matrix specific events"""

from opsdroid.events import Event


class MatrixStateEvent(Event):
    """A Generic matrix state event."""

    def __init__(self, key, content, *args, state_key=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.key = key
        self.content = content
        self.state_key = state_key

    def __repr__(self):
        return f"<MatrixStateEvent(room_id={self.target}, key={self.key}, content={self.content})>"


class MatrixPowerLevels(MatrixStateEvent):
    """Send power levels."""

    def __init__(self, power_levels, *args, **kwargs):
        key = "m.room.power_levels"
        super().__init__(key, power_levels, *args, **kwargs)


class MatrixJoinRules(MatrixStateEvent):
    def __init__(self, join_rule, *args, **kwargs):
        key = "m.room.join_rules"
        content = {"join_rule": join_rule}
        super().__init__(key, content, *args, **kwargs)


class MatrixHistoryVisibility(MatrixStateEvent):
    def __init__(self, history_visibility, *args, **kwargs):
        key = "m.room.history_visibility"
        content = {"history_visibility": history_visibility}
        super().__init__(key, content, *args, **kwargs)


class MatrixRoomAvatar(MatrixStateEvent):
    def __init__(self, url, *args, **kwargs):
        key = "m.room.avatar"
        content = {"url": url}
        super().__init__(key, content, *args, **kwargs)
