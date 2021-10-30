# -*- coding: utf-8 -*-
"""A module for opsdroid to allow persist in postgres database."""
import logging
import json
import asyncpg

from contextlib import asynccontextmanager
from opsdroid.database import Database
from opsdroid.helper import JSONEncoder, JSONDecoder
from voluptuous import Any, Required

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = {
    "host": str,
    "port": Any(int, str),
    "database": str,
    "user": str,
    Required("password"): str,
    "table": str,
}


def create_table_if_not_exists(func):
    """Decorator to check if the table specified exists.
    Creates table if it does not exist.
    """

    async def create_table_query(connection, table):
        await connection.execute(
            'CREATE TABLE IF NOT EXISTS "{}" ( key text PRIMARY KEY, data JSONb)'.format(
                table
            )
        )
        await connection.execute(
            'CREATE INDEX IF NOT EXISTS idxgin ON "{}" USING gin (data);'.format(table)
        )

    async def wrapper(*args, **kwargs):
        # args[0].connection will get DatabasePostgresql.connection
        connection = args[0].connection
        table = args[0].table

        if " " in table:

            _LOGGER.warning(
                f"Table contains a space character. Consider changing '{table}' to {table.strip(' ')}"
             )
                f"Table contains a space character. Consider changing '{table}' to {table.strip(' ')}"
            )

        try:
            await create_table_query(connection, table)
            return await func(*args, **kwargs)
        except Exception as error:
            _LOGGER.exception("PostgresSQL Could not create table %s", table)
            return None

    return wrapper


def check_table_format(func):
    """Decorator to check the format of the table for proper fields.
    Creates table if it does not exist"""

    async def get_table_structure_query(connection, table):
        # async with connection.transaction():
        # Check Table's data structure is correct
        return await connection.fetch(
            "SELECT column_name,data_type FROM information_schema.columns WHERE table_name = '{}'".format(
                table
            )
        )

    async def wrapper(*args, **kwargs):
        # args[0].connection will get DatabasePostgresql.connection
        connection = args[0].connection
        table = args[0].table

        try:
            data_structure = await get_table_structure_query(connection, table)

            key_column = [
                data
                for data in data_structure
                if data["column_name"] == "key" and data["data_type"] == "text"
            ][0]
            data_column = [
                data
                for data in data_structure
                if data["column_name"] == "data" and data["data_type"] == "jsonb"
            ][0]
            if key_column and data_column:
                _LOGGER.debug(
                    "PostgresSQL table %s verified correct data structure", table
                )
            return await func(*args, **kwargs)
        except Exception:
            _LOGGER.error("PostgresSQL table %s has incorrect data structure", table)
            return None

    return wrapper


class DatabasePostgresql(Database):
    """A module for opsdroid to allow memory to persist in a PostgreSQL database."""

    def __init__(self, config, opsdroid=None):
        """Create the connection.

        Args:
            config (dict): The config for this database specified in the
                           `configuration.yaml` file.
            opsdroid (OpsDroid): An instance of opsdroid.core.

        """
        super().__init__(config, opsdroid=opsdroid)
        _LOGGER.debug("Loaded PostgreSQL database connector.")
        self.name = "postgresql"
        self.config = config
        self.connection = None
        self.table = self.config.get("table", "opsdroid")

    async def connect(self):
        """Connect to the database."""
        host = self.config.get("host", "localhost")
        port = self.config.get("port", 5432)
        database = self.config.get("database", "opsdroid")
        user = self.config.get("user", "opsdroid")
        pwd = self.config.get("password")
        self.connection = await asyncpg.connect(
            user=user, password=pwd, database=database, host=host, port=port
        )
        _LOGGER.info("Connected to PostgreSQL.")

    async def disconnect(self):
        """Disconnect from the database."""
        if self.connection:
            await self.connection.close()
            _LOGGER.info("Disconnected from PostgreSQL.")

    @create_table_if_not_exists
    @check_table_format
    async def put(self, key, data):
        """Insert or replace an object into the database for a given key.

        Args:
            key (str): the key is the key field in the table.
            data (object): the data to be inserted or replaced

        """

        _LOGGER.debug("Putting %s into PostgreSQL table %s", key, self.table)
        if isinstance(data, str):
            data = {"value": data}
        json_data = json.dumps(data, cls=JSONEncoder)
        await self.put_query(key, json_data)

    async def put_query(self, key, json_data):
        """SQL transaction to write data to the specified table"""
        key_already_exists = await self.get(key)
        if key_already_exists:
            await self.connection.execute(
                'UPDATE "{}" SET data = $2 WHERE key = $1'.format(self.table),
                key,
                json_data,
            )
        else:
            await self.connection.execute(
                'INSERT INTO "{}" (key, data) VALUES ($1, $2)'.format(self.table),
                key,
                json_data,
            )

    @check_table_format
    async def get(self, key):
        """Get a document from the database (key).

        Args:
            key (str): the key is the key field in the table.

        """

        _LOGGER.debug("Getting %s from PostgreSQL table %s", key, self.table)

        values = await self.get_query(key)

        if len(values) > 1:
            _LOGGER.error(f"{len(values) entries with the same key name '{values}', in PostgressSQL table {self.table}. Only one is allowed.")
                str(len(values))
                + " entries with same key name in PostgresSQL table %s. Only one allowed.",
                self.table,
            )
            return None

        if (len(values) == 1) and values[0]["data"]:
            data = json.loads(values[0]["data"], object_hook=JSONDecoder())
            if data.keys() == {"value"}:
                data = data["value"]
            return data

        return None

    async def get_query(self, key):
        """SQL transaction to get data from the specified table."""
        return await self.connection.fetch(
            'SELECT data FROM "{}" WHERE key = $1'.format(self.table),
            key,
        )

    @check_table_format
    async def delete(self, key):
        """Delete a record from the database (key).

        Args:
            key (str): the key is the key field in the table.

        """

        _LOGGER.debug("Deleting %s from PostgreSQL table %s.", key, self.table)
        await self.delete_query(key)

    async def delete_query(self, key):
        """SQL transaction to delete data from the specified table."""
        # async with self.connection.transaction():
        await self.connection.execute(
            'DELETE FROM "{}" WHERE key = $1'.format(self.table), key
        )

    @asynccontextmanager
    async def memory_in_table(self, table):
        """Use the specified table rather than the default."""
        db_copy = DatabasePostgresql(self.config, self.opsdroid)
        try:
            await db_copy.connect()
            db_copy.table = table
            yield db_copy
        finally:
            await db_copy.disconnect()
