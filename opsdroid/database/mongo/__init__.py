# -*- coding: utf-8 -*-
"""A module for opsdroid to allow persist in mongo database."""
import logging
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from voluptuous import Any

from opsdroid.database import Database

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = {
    "host": str,
    "port": Any(int, str),
    "database": str,
    "user": str,
    "password": str,
    "collection": str,
}


class DatabaseMongo(Database):
    """A module for opsdroid to allow memory to persist in a mongo database."""

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
        _LOGGER.debug("Loaded mongo database connector.")
        self.name = "mongo"
        self.config = config
        self.client = None
        self.database = None
        self.collection = config.get("collection", "opsdroid")

    async def connect(self):
        """Connect to the database."""
        host = self.config.get("host", "localhost")
        protocol = self.config.get("protocol", "mongodb").replace("://", "")
        port = self.config.get("port", "27017")
        if port != "27017":
            host = f"{host}:{port}"
        database = self.config.get("database", "opsdroid")
        user = self.config.get("user")
        pwd = self.config.get("password")
        if user and pwd:
            self.db_url = f"{protocol}://{user}:{pwd}@{host}"
        else:
            self.db_url = f"{protocol}://{host}"
        self.client = AsyncIOMotorClient(self.db_url)
        self.database = self.client[database]
        _LOGGER.info("Connected to MongoDB.")

    async def put(self, key, data):
        """Insert or replace an object into the database for a given key.

        Args:
            key (str): the key is the document lookup key.
            data (object): the data to be inserted or replaced

        """
        _LOGGER.debug("Putting %s into MongoDB collection %s", key, self.collection)

        if isinstance(data, str):
            data = {"value": data}
        if "key" not in data:
            data["key"] = key

        return await self.database[self.collection].update_one(
            {"key": data["key"]}, {"$set": data}, upsert=True
        )

    async def get(self, key):
        """Get a document from the database (key).

        Args:
            key (str): the key is the document lookup key.

        """
        _LOGGER.debug("Getting %s from MongoDB collection %s", key, self.collection)

        response = await self.database[self.collection].find_one(
            {"$query": {"key": key}, "$orderby": {"$natural": -1}}
        )
        if response.keys() == {"_id", "key", "value"}:
            response = response["value"]
        return response

    async def delete(self, key):
        """Delete a document from the database (key).

        Args:
            key (str): the key is the document lookup key.

        """
        _LOGGER.debug("Deleting %s from MongoDB collection %s.", key, self.collection)

        return await self.database[self.collection].delete_one({"key": key})

    @asynccontextmanager
    async def memory_in_collection(self, collection):
        """Use the specified collection rather than the default."""
        db_copy = DatabaseMongo(self.config, self.opsdroid)
        try:
            await db_copy.connect()
            db_copy.collection = collection
            yield db_copy
        finally:
            if db_copy.client:
                db_copy.client.close()
