import logging

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
        self.should_encrypt = config.get("should_encrypt", True)
        self._event_type = "dev.opsdroid.database"
        self.should_migrate = True

        _LOGGER.debug("Loaded matrix database connector.")

    @property
    def connector(self):
        return self.opsdroid.get_connector("matrix")

    @property
    def room_id(self):
        return (
            self.room
            if self.room.startswith("!")
            else self.connector.room_ids[self.room]
        )

    async def migrate_database(self):
        """Migrate existing 'opsdroid.database' state event to 'dev.opsdroid.database' event"""

        data = await self.connector.connection.room_get_state(room_id=self.room_id)
        if isinstance(data, RoomGetStateError):
            _LOGGER.error(
                "Error migrating from opsdroid.database to {self._event_type} in room {self.room_id}: {data.message}({data.status_code})"
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
        """Insert or replace an value into the database for a given key."""

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
                "Error putting key into matrix room {self.room_id}: {ori_data.message}({ori_data.status_code})"
            )
            return
        ori_data = ori_data.content

        if self._single_state_key:
            value = {key: value}

        elif not isinstance(value, dict):
            raise ValueError("When single_state_key is False value must be a dict.")

        if list(value.keys())[0] in ori_data:
            existing_val = await self.get(key)
            if existing_val == ori_data[list(value.keys())[0]]:
                _LOGGER.debug("Not updating matrix state, as content hasn't changed.")
                return

        if self.should_encrypt:
            room_event = await self.opsdroid.send(
                GenericMatrixRoomEvent(content=value, event_type=self._event_type)
            )
            data = {**ori_data, key: room_event.event_id}
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

    async def get(self, state_key=None, key=None):
        """Get a value from the database for a given key."""

        if self.should_migrate:
            await self.migrate_database()

        if not self._single_state_key and not state_key:
            _LOGGER.error(
                "When single_state_key is false, a state_key must be provided to find from."
            )
            return None

        if not state_key and not key:
            _LOGGER.error("No key provided to search for.")
            return None

        # If the single state key flag is set then use that else use state key.
        state_key = (
            ""
            if self._single_state_key is True
            else self._single_state_key or state_key
        )

        _LOGGER.debug(
            f"Getting {key} from matrix room {self.room_id} with state_key={state_key}."
        )

        data = await self.connector.connection.room_get_state_event(
            room_id=self.room_id, event_type=self._event_type, state_key=state_key,
        )
        if isinstance(data, RoomGetStateEventError):
            _LOGGER.error(
                "Error getting {key} from matrix room {self.room_id}: {data.message}({data.status_code})"
            )
            return
        data = data.content

        _LOGGER.debug(f"Got {data} from state request.")

        if not data:
            return None

        try:
            if key:
                data = data[key]
        except KeyError:
            _LOGGER.debug("{key or state_key} doesn't exist in database")
            return None

        if self.should_encrypt:
            resp = await self.connector.connection.room_get_event(
                room_id=self.room_id, event_id=data,
            )
            data = resp.event.source["content"][key]

        return data

    async def delete(self, state_key=None, key=None):
        """Delete a key from the database."""

        if self.should_migrate:
            await self.migrate_database()

        if not self._single_state_key and not state_key:
            _LOGGER.error(
                "When single_state_key is false, a state_key must be provided to delete from."
            )
            return None

        if not state_key and not key:
            _LOGGER.error("No key provided for deletion.")
            return None

        # If the single state key flag is set then use that else use state key.
        state_key = (
            ""
            if self._single_state_key is True
            else self._single_state_key or state_key
        )

        _LOGGER.debug("Deleting {key or state_key} from {room_id}")

        data = await self.connector.connection.room_get_state_event(
            room_id=self.room_id, event_type=self._event_type, state_key=state_key,
        )
        if isinstance(data, RoomGetStateEventError):
            _LOGGER.error(
                "Error deleting {key} from matrix room {self.room_id}: {data.message}({data.status_code})"
            )
            return
        data = data.content

        _LOGGER.debug(f"Got {data} from state request.")

        if not data:
            return None

        try:
            if not key:
                return_value = data.copy()
                data.clear()
            else:
                return_value = data[key]
                del data[key]
        except KeyError:
            _LOGGER.debug("Not deleting {key or state_key}, as it doesn't exist")
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
