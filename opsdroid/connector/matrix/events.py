"""Matrix specific events."""
import warnings

from opsdroid.events import Event


__all__ = [
    "GenericMatrixRoomEvent",
    "MatrixRoomAvatar",
    "MatrixHistoryVisibility",
    "MatrixJoinRules",
    "MatrixPowerLevels",
    "MatrixStateEvent",
]


class GenericMatrixRoomEvent(Event):
    """A generic matrix room event.

    Used for things which don't have a specific event type or as a base for
    matrix specific events.
    """

    def __init__(self, event_type, content, *args, **kwargs):  # noqa: D107
        super().__init__(*args, **kwargs)
        self.content = content
        self.event_type = event_type

    def __repr__(self):  # noqa: D105
        return f"<GenericMatrixRoomEvent(room_id={self.target}, event_type={self.event_type}, content={self.content})>"


class MatrixStateEvent(GenericMatrixRoomEvent):
    """A Generic matrix state event."""

    def __init__(self, *args, state_key=None, **kwargs):  # noqa: D107
        super().__init__(*args, **kwargs)
        self.state_key = state_key

    def __repr__(self):  # noqa: D105
        return f"<MatrixStateEvent(room_id={self.target}, event_type={self.event_type}, state_key={self.state_key}, content={self.content})>"


class MatrixPowerLevels(MatrixStateEvent):
    """Send power levels."""

    # Deprecate old name for event_type
    @property
    def key(self):  # noqa: D401
        """Deprecated alias for event_type."""
        warnings.warn(
            "key has been renamed event_type to reduce confusion with state_key",
            DeprecationWarning,
        )  # pragma: nocover
        return self.event_type  # pragma: nocover

    @key.setter
    def _(self, val):
        self.event_type = key  # pragma: nocover

    def __init__(self, power_levels, *args, **kwargs):  # noqa: D107
        event_type = "m.room.power_levels"
        super().__init__(event_type, power_levels, *args, **kwargs)


class MatrixJoinRules(MatrixStateEvent):
    """The room's join rules."""

    def __init__(self, join_rule, *args, **kwargs):  # noqa: D107
        event_type = "m.room.join_rules"
        content = {"join_rule": join_rule}
        super().__init__(event_type, content, *args, **kwargs)


class MatrixHistoryVisibility(MatrixStateEvent):
    """The room's history visibility."""

    def __init__(self, history_visibility, *args, **kwargs):  # noqa: D107
        event_type = "m.room.history_visibility"
        content = {"history_visibility": history_visibility}
        super().__init__(event_type, content, *args, **kwargs)


class MatrixRoomAvatar(MatrixStateEvent):
    """The room's avatar."""

    def __init__(self, url, *args, **kwargs):  # noqa: D107
        event_type = "m.room.avatar"
        content = {"url": url}
        super().__init__(event_type, content, *args, **kwargs)
