"""Module for storing data within Redis."""
from datetime import date, datetime
import json
import time

import asyncio_redis

from opsdroid.database import Database


class RedisDatabase(Database):
    """Database class for storing data within a Redis instance."""

    def __init__(self, config, opsdroid=None):
        """Initialise the sqlite database.

        Set basic properties of the database. Initialise properties like
        name, connection arguments, database file, table name and config.

        Args:
            config (dict): The configuration of the database which consists
                           of `file` and `table` name of the sqlite database
                           specified in `configuration.yaml` file.

        """
        super().__init__(config, opsdroid=opsdroid)
        self.config = config
        self.client = None
        self.host = self.config.get("host", "localhost")
        self.port = self.config.get("port", 6379)
        self.database = self.config.get("database", 0)
        self.password = self.config.get("password", None)
        self.reconnect = self.config.get("reconnect", False)

    async def connect(self):
        """Connect to the database.

        This method will connect to a Redis database. By default it will
        connect to Redis on localhost on port 6379

        """
        self.client = await asyncio_redis.Connection.create(
            host=self.host,
            port=self.port,
            db=self.database,
            auto_reconnect=self.reconnect,
            password=self.password,
        )

    async def put(self, key, data):
        """Store the data object in Redis against the key.

        Args:
            key (string): The key to store the data object under.
            data (object): The data object to store.

        """
        data = self.convert_object_to_timestamp(data)
        await self.client.set(key, json.dumps(data))

    async def get(self, key):
        """Get data from Redis for a given key.

        Args:
            key (string): The key to lookup in the database.

        Returns:
            object or None: The data object stored for that key, or None if no
                            object found for that key.

        """
        data = await self.client.get(key)

        if data:
            return self.convert_timestamp_to_object(json.loads(data))

        return None

    async def disconnect(self):
        """Disconnect from the database."""
        self.client.close()

    @staticmethod
    def convert_object_to_timestamp(data):
        """
        Serialize dict before storing into Redis.

        Args:
            dict: Dict to serialize

        Returns:
            dict: Dict from redis to unserialize

        """
        for k, value in data.items():
            if isinstance(value, (datetime, date)):
                value = '::'.join([
                    type(value).__name__,
                    '%d' % time.mktime(value.timetuple())
                ])
                data[k] = value
        return data

    @staticmethod
    def convert_timestamp_to_object(data):
        """
        Unserialize data from Redis.

        Args:
            dict: Dict from redis to unserialize

        Returns:
            dict: Dict to serialize

        """
        for k, value in data.items():
            value_type = value.split('::', 1)[0]
            if value_type == 'datetime':
                timestamp = int(value.split('::', 1)[1])
                value = datetime.fromtimestamp(timestamp)
            elif value_type == 'date':
                timestamp = int(value.split('::', 1)[1])
                value = date.fromtimestamp(timestamp)
            data[k] = value
        return data
