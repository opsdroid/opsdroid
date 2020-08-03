"""Database that uses the matrix connector."""

import logging
from contextlib import contextmanager

from nio import RoomGetStateError, RoomGetStateEventError
from opsdroid.database import Database
from opsdroid.connector.matrix.events import MatrixStateEvent, GenericMatrixRoomEvent

_LOGGER = logging.getLogger(__name__)


class DatabaseMatrix(Database):
    """A module for opsdroid to allow memory to persist in matrix room state."""

    def __init__(self, config, opsdroid=None):
        """Start the database connection."""
        super().__init__(config, opsdroid=opsdroid)
        self.name = "matrix"
        self.room = config.get("default_room", "main")
        self._single_state_key = config.get("single_state_key", True)
        self.should_encrypt = config.get("should_encrypt", False)
        self._event_type = "dev.opsdroid.database"
        self.should_migrate = True

        _LOGGER.debug("Loaded matrix database connector.")

    @property
    def connector(self):
        """Define the initiated matrix connector."""
        return self.opsdroid.get_connector("matrix")

    @property
    def room_id(self):
        """Define ID of the room to store data in."""
        return (
            self.room
            if self.room.startswith("!")
            else self.connector.room_ids[self.room]
        )

    async def migrate_database(self):
        """Migrate existing 'opsdroid.database' state event to 'dev.opsdroid.database' event."""

        data = await self.connector.connection.room_get_state(room_id=self.room_id)
        if isinstance(data, RoomGetStateError):
            _LOGGER.error(
                f"Error migrating from opsdroid.database to {self._event_type} in room {self.room_id}: {data.message}({data.status_code})"
            )
            return

        if not any(event["type"] == self._event_type for event in data.events):
            for event in data.events:
                if event["type"] == "opsdroid.database":
                    await self.connector.connection.room_put_state(
                        room_id=self.room_id,
                        event_type=self._event_type,
                        content=event["content"],
                        state_key=event["state_key"],
                    )
                    await self.connector.connection.room_redact(
                        room_id=self.room_id, event_id=event["event_id"],
                    )

        self.should_migrate = False

    async def connect(self):
        """Connect to the database."""

        _LOGGER.info("Matrix Database connector initialised.")

    async def put(self, key, value):
        """Insert or replace a value into the database for a given key."""

        if self.should_migrate:
            await self.migrate_database()

        # If the single state key flag is set then use that else use state key.
        state_key = (
            "" if self._single_state_key is True else self._single_state_key or key
        )

        _LOGGER.debug(f"Putting {key} into matrix room {self.room_id}.")

        ori_data = await self.connector.connection.room_get_state_event(
            room_id=self.room_id, event_type=self._event_type, state_key=state_key,
        )
        if isinstance(ori_data, RoomGetStateEventError):
            _LOGGER.error(
                f"Error putting key into matrix room {self.room_id}: {ori_data.message}({ori_data.status_code})"
            )
            return
        ori_data = ori_data.content

        if self._single_state_key:
            value = {key: value}

        elif not isinstance(value, dict):
            raise ValueError(
                "When the matrix database is configured with single_state_key=False, "
                "the value passed must be a dict."
            )

        sub_key = list(value.keys())[0]

        if list(value.keys())[0] in ori_data:
            if self._single_state_key:
                existing_val = await self.get(sub_key)
            else:
                existing_val = await self.get({key: sub_key})
            if existing_val == value[sub_key]:
                _LOGGER.debug("Not updating matrix state, as content hasn't changed.")
                return

        if self.should_encrypt:
            room_event = await self.opsdroid.send(
                GenericMatrixRoomEvent(content=value, event_type=self._event_type)
            )
            data = {**ori_data, sub_key: {"encrypted_val": room_event.event_id}}
        else:
            data = {**ori_data, **value}

        _LOGGER.debug(f"Putting {key} into matrix room {self.room_id} with {data}")

        await self.opsdroid.send(
            MatrixStateEvent(
                self._event_type,
                content=data,
                target=self.room_id,
                connector=self.connector,
                state_key=state_key,
            )
        )

        return True

    async def get(self, key):
        """Get a value from the database for a given key."""

        if self.should_migrate:
            await self.migrate_database()

        if not self._single_state_key and not isinstance(key, dict):
            _LOGGER.error(
                "When the matrix database is configured with single_state_key=False, key must be a dict."
            )

        # If the single state key flag is set then use that else use state key.
        state_key = (
            "" if self._single_state_key is True else self._single_state_key or key
        )

        if isinstance(state_key, dict):
            state_key, key = list(state_key.items())[0]

        _LOGGER.debug(
            f"Getting {key} from matrix room {self.room_id} with state_key={state_key}."
        )

        data = await self.connector.connection.room_get_state_event(
            room_id=self.room_id, event_type=self._event_type, state_key=state_key,
        )
        if isinstance(data, RoomGetStateEventError):
            _LOGGER.error(
                f"Error getting {key} from matrix room {self.room_id}: {data.message}({data.status_code})"
            )
            return
        data = data.content

        _LOGGER.debug(f"Got {data} from state request.")

        for k, v in data.items():
            if isinstance(v, dict) and "encrypted_val" in v:
                resp = await self.connector.connection.room_get_event(
                    room_id=self.room_id, event_id=v["encrypted_val"],
                )
                data[k] = resp.event.source["content"][k]

        try:
            data = data[key]
        except KeyError:
            _LOGGER.debug(f"{key} doesn't exist in database")
            return None

        return data

    async def delete(self, key):
        """Delete a key from the database."""

        if self.should_migrate:
            await self.migrate_database()

        if not self._single_state_key and not isinstance(key, dict):
            _LOGGER.error(
                "When the matrix database is configured with single_state_key=False, key must be a dict."
            )

        # If the single state key flag is set then use that else use state key.
        state_key = (
            "" if self._single_state_key is True else self._single_state_key or key
        )

        if isinstance(state_key, dict):
            state_key, key = list(state_key.items())[0]

        _LOGGER.debug(f"Deleting {key} from {room_id}")

        data = await self.connector.connection.room_get_state_event(
            room_id=self.room_id, event_type=self._event_type, state_key=state_key,
        )
        if isinstance(data, RoomGetStateEventError):
            _LOGGER.error(
                f"Error deleting {key} from matrix room {self.room_id}: {data.message}({data.status_code})"
            )
            return
        data = data.content

        _LOGGER.debug(f"Got {data} from state request.")

        try:
            if self._single_state_key:
                return_value = data[key]
                del data[key]
            else:
                return_value = data.copy()
                data.clear()
        except KeyError:
            _LOGGER.debug(f"Not deleting {key}, as it doesn't exist")
            return None

        await self.opsdroid.send(
            MatrixStateEvent(
                self._event_type,
                content=data,
                target=self.room_id,
                connector=self.connector,
                state_key=state_key,
            )
        )

        return return_value

    @contextmanager
    def memory_in_room(self, room):
        """Switch to a different room for some operations."""
        ori_room = self.room
        self.room = room
        yield
        self.room = ori_room
