# -*- coding: utf-8 -*-
"""A module for opsdroid to allow persist in mongo database."""
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from voluptuous import Any

from opsdroid.database import Database

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = {"host": str, "port": Any(int, str), "database": str}


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

    async def connect(self):
        """Connect to the database."""
        host = self.config.get("host", "localhost")
        port = self.config.get("port", "27017")
        database = self.config.get("database", "opsdroid")
        path = "mongodb://{host}:{port}".format(host=host, port=port)
        self.client = AsyncIOMotorClient(path)
        self.database = self.client[database]
        _LOGGER.info("Connected to MongoDB.")

    async def put(self, key, data):
        """Insert or replace an object into the database for a given key.

        Args:
            key (str): the key is the databasename
            data (object): the data to be inserted or replaced

        """
        _LOGGER.debug("Putting %s into MongoDB.", key)
        if "_id" in data:
            await self.database[key].update_one({"_id": data["_id"]}, {"$set": data})
        else:
            await self.database[key].insert_one(data)

    async def get(self, key):
        """Get a document from the database (key).

        Args:
            key (str): the key is the database name.

        """
        _LOGGER.debug("Getting %s from MongoDB.", key)
        return await self.database[key].find_one(
            {"$query": {}, "$orderby": {"$natural": -1}}
        )

    async def delete(self, key):
        """Delete a document from the database (key).

        Args:
            key (str): the key is the database name.

        """
        _LOGGER.debug("Deleting %s from MongoDB.", key)
        return await self.database[key].delete_one({"$query": {}})
