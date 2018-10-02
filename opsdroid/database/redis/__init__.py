"""Module for storing data within Redis."""
from datetime import date, datetime
import json
import time

import aioredis

from opsdroid.database import Database


class RedisDatabase(Database):
    """Database class for storing data within a Redis instance."""

    client = None
    _connect = lambda *args, **kwargs: aioredis.create_connection(*args[1:], **kwargs)

    async def connect(self, opsdroid):
        """Connect to the database.

        This method will connect to a Redis database. By default it will
        connect to Redis on localhost on port 6379

        Args:
            opsdroid (OpsDroid): An instance of opsdroid core.

        """
        host = self.config.get("host", "localhost")
        port = self.config.get("port", "6379")
        database = self.config.get("database", 0)
        self.client = await self._connect((host, port), db=database)

    async def put(self, key, data):
        """Store the data object in Redis against the key.

        Args:
            key (string): The key to store the data object under.
            data (object): The data object to store.

        """
        data = self.convert_object_to_timestamp(data)
        await self.client.execute('SET', key, json.dumps(data))

    async def get(self, key):
        """Get data from Redis for a given key.

        Args:
            key (string): The key to lookup in the database.

        Returns:
            object or None: The data object stored for that key, or None if no
                            object found for that key.

        """
        data = await self.client.execute('GET', key, encoding="utf-8")

        if data:
            return self.convert_timestamp_to_object(json.loads(data))

        return None

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
