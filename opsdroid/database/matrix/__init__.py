"""Database that uses the matrix connector."""

import logging
from contextlib import contextmanager
from wrapt import decorator

from nio import RoomGetStateError, RoomGetStateEventError, RoomGetEventError
from opsdroid.database import Database
from opsdroid.helper import get_opsdroid
from opsdroid.connector.matrix.events import MatrixStateEvent, GenericMatrixRoomEvent
from voluptuous import Any

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = {
    "default_room": str,
    "single_state_key": Any(bool, str),
    "should_encrypt": bool,
}


@decorator
async def memory_in_event_room(func, instance, args, kwargs):
    """Use room state from the room the message was received in rather than the default."""

    database = get_opsdroid().get_database("matrix")
    message = args[-1]

    if not database:
        return await func(*args, **kwargs)
    with database.memory_in_room(message.target):
        return await func(*args, **kwargs)


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
        """Define the initiated matrix connector."""
        return self.opsdroid.get_connector("matrix")

    @property
    def room_id(self):
        """Define ID of the room to store data in."""
        return self.connector.lookup_target(self.room)

    @property
    def is_room_encrypted(self):
        """Check if room is encrypted."""
        return (
            self.connector._allow_encryption
            and self.room_id in self.connector.connection.store.load_encrypted_rooms()
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
                if event["type"] == "opsdroid.database" and event["content"]:
                    if not self._single_state_key:
                        event["content"] = {event["state_key"]: event["content"]}
                    await self.opsdroid.send(
                        MatrixStateEvent(
                            self._event_type,
                            content=event["content"],
                            target=self.room_id,
                            connector=self.connector,
                            state_key=event["state_key"],
                        )
                    )
                    await self.connector.connection.room_redact(
                        room_id=self.room_id, event_id=event["event_id"]
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

        value = {key: value}

        data = await self.get(key, get_full=True) or {}

        if {**data, **value} == data:
            _LOGGER.error("Not updating matrix state, as content hasn't changed.")
            return
        else:
            data = {**data, **value}

        if self.is_room_encrypted and self.should_encrypt:
            room_event = await self.opsdroid.send(
                GenericMatrixRoomEvent(
                    target=self.room_id, content=value, event_type=self._event_type
                )
            )
            data[key] = {"encrypted_val": room_event.event_id}

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

    async def get(self, key, get_full=False):
        """Get a value from the database for a given key.

        params:
            key (str): Key to retrieve value for.
            get_full (bool): Parameter for internal use(needed for `put`).

        """

        if self.should_migrate:
            await self.migrate_database()

        # If the single state key flag is set then use that else use state key.
        state_key = (
            "" if self._single_state_key is True else self._single_state_key or key
        )

        _LOGGER.debug(
            f"Getting {key} from matrix room {self.room_id} with state_key={state_key}."
        )

        ori_data = await self.connector.connection.room_get_state_event(
            room_id=self.room_id, event_type=self._event_type, state_key=state_key
        )

        if isinstance(ori_data, RoomGetStateEventError):
            if (
                ori_data.transport_response is not None
                and ori_data.transport_response.status == 404
            ):
                _LOGGER.error(
                    f"Error getting {key} from matrix room {self.room_id}: Event not found"
                )
                return
            raise RuntimeError(
                f"Error getting {key} from matrix room {self.room_id}: {ori_data.message}({ori_data.status_code})"
            )

        data = ori_data.content

        _LOGGER.debug(f"Got {data} from state in room {self.room_id}")

        if self._single_state_key:
            if key in data:
                data = {key: data[key]}
            elif not get_full:
                _LOGGER.debug(
                    f"{key} doesn't exist in state event in room {self.room_id}."
                )
                return
            else:
                return data

        for k, v in data.items():
            if isinstance(v, dict) and len(v) == 1 and "encrypted_val" in v:
                resp = await self.connector.connection.room_get_event(
                    room_id=self.room_id, event_id=v["encrypted_val"]
                )
                if isinstance(resp, RoomGetEventError):
                    _LOGGER.error(
                        f"Error decrypting event {v['encrypted_val']} while getting "
                        f"{key}: {resp.message}({resp.status_code})"
                    )
                    continue
                data[k] = resp.event.source["content"][k]

        if get_full:
            return {**ori_data.content, **data}

        return data[key]

    async def delete(self, key):
        """Delete a key from the database.

        params:
            key (str | List[str]): Key to delete from the database. Can be a list of keys if single_state_key is True

        """

        if self.should_migrate:
            await self.migrate_database()

        # If the single state key flag is set then use that else use state key.
        state_key = (
            "" if self._single_state_key is True else self._single_state_key or key
        )

        data = await self.connector.connection.room_get_state_event(
            room_id=self.room_id, event_type=self._event_type, state_key=state_key
        )
        if isinstance(data, RoomGetStateEventError):
            _LOGGER.error(
                f"Error deleting {key} from matrix room {self.room_id}: {data.message}({data.status_code})"
            )
            return

        if (
            data.transport_response is not None
            and data.transport_response.status == 404
        ):
            _LOGGER.error(
                f"State event {self._event_type} with state key '{state_key}' doesn't exist."
            )
            return

        data = data.content

        _LOGGER.debug(f"Got {data} from state event in room {self.room_id}.")

        if not isinstance(key, list):
            key = [key]

        return_value = []
        for k in key:  # key can be a list of keys to delete
            try:
                return_value.append(data[k])
                _LOGGER.debug(f"Deleting key '{k}' from database in {self.room_id}.")
                del data[k]
            except KeyError:
                _LOGGER.warning(
                    f"Unable to delete '{k}' from database in room {self.room_id} as it doesn't exist."
                )

        await self.opsdroid.send(
            MatrixStateEvent(
                self._event_type,
                content=data,
                target=self.room_id,
                connector=self.connector,
                state_key=state_key,
            )
        )

        if not return_value:
            return None
        elif len(return_value) == 1:
            return return_value[0]
        else:
            return return_value

    @contextmanager
    def memory_in_room(self, room):
        """Use room state in the given room rather than the default."""
        ori_room = self.room
        self.room = room
        yield
        self.room = ori_room
