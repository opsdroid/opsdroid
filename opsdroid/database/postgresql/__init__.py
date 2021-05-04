# -*- coding: utf-8 -*-
"""A module for opsdroid to allow persist in postgres database."""
import logging
import json
import asyncpg

from opsdroid.database import Database
from opsdroid.helper import JSONEncoder, JSONDecoder

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = {"host": str, "password": str, "port": int, "database": str}

def check_table(func):
    """Decorator to check if the table specified exists and has correct format.
    Creates table if it does not exist"""
    async def wrapper(*args, **kwargs):
        # args[0].connection will get DatabasePostgres.connection
        connection = args[0].connection
        if 'table_name' in kwargs:
            table_name = kwargs['table_name']
        else:
            table_name = 'opsdroid_default'

        async with connection.transaction():
            # Create table if it does not exist
            await connection.execute(
                'CREATE TABLE IF NOT EXISTS {} ( key text PRIMARY KEY, data text)'.format(table_name)
            )

            # Check Table's data structure is correct
            data_structure = await connection.fetch(
                'SELECT column_name,data_type FROM information_schema.columns WHERE table_name = \'{}\''.format(table_name)
            )
            valid = len(data_structure) == 2
            valid &= data_structure[0]['column_name'] == 'key' and data_structure[0]['data_type'] == 'text'
            valid &= data_structure[1]['column_name'] == 'data' and data_structure[1]['data_type'] == 'text'
            if not valid:
                _LOGGER.error('PostgresSQL table {} has incorrect data structure'.format(table_name))
        return await func(*args, **kwargs)
    return wrapper

class DatabasePostgres(Database):
    """A module for opsdroid to allow memory to persist in a PostgreSQL database."""

    def __init__(self, config, opsdroid=None):
        """Create the connection.

        Set some basic properties from the database config such as the name
        of this database.

        Args:
            config (dict): The config for this database specified in the
                           `configuration.yaml` file.
            opsdroid (OpsDroid): An instance of opsdroid.core.

        """
        super().__init__(config, opsdroid=opsdroid)
        _LOGGER.debug("Loaded PostgreSQL database connector.")
        self.name = "postgres"
        self.config = config
        self.connection = None
        self.user = self.config.get("user", "opsdroid")
        self.password = self.config.get("password")
        self.database = self.config.get("database", "opsdroid")
        self.host = self.config.get("host", "localhost")

        _LOGGER.debug("Loaded postgres database connector")

    async def connect(self):
        self.connection = await asyncpg.connect(
            user=self.user,
            password=self.password,
            database=self.database,
            host=self.host
        )

    async def disconnect(self):
        await self.connection.close()

    @check_table
    async def put(self, key, data, table_name='opsdroid_default'):
        """Insert or replace an object into the database for a given key.

        Args:
            key (str): the key is the databasename
            data (object): the data to be inserted or replaced

        """
        _LOGGER.debug("Putting %s into PostgreSQL", key)

        json_data = json.dumps(data, cls=JSONEncoder)

        async with self.connection.transaction():
            await self.connection.execute(
                "UPDATE {} SET data = $2 WHERE key = $1".format(table_name),
                key, json_data
            )

    @check_table
    async def get(self, key, table_name='opsdroid_default'):
        """Get a document from the database (key).

        Args:
            key (str): the key is the database name.

        """
        _LOGGER.debug("Getting %s from PostgreSQL.", key)

        values = await self.connection.fetch(
            'SELECT data FROM {} WHERE key = $1'.format(table_name),
            key,
        )

        if (len(values) == 1) and values[0]['data']:
            data = json.loads(values[0]['data'], object_hook=JSONDecoder())
            return data
        elif len(values) > 1:
            _LOGGER.error(str(len(values)) + ' entries with same key name in PostgresSQL table {}'.format(table_name))
        else:
            return None

    @check_table
    async def delete(self, key, table_name='opsdroid_default'):
        """Delete a document from the database (key).

        Args:
            key (str): the key is the database name.

        """
        _LOGGER.debug("Deleting %s from PostgreSQL.", key)

        async with self.connection.transaction():
            await self.connection.execute(
                "DELETE FROM {} WHERE key = $1".format(table_name),
                key
            )
