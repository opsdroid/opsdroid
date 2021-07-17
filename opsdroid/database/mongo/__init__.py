# -*- coding: utf-8 -*-
"""A module for opsdroid to allow persist in mongo database."""
import logging
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
        port = self.config.get("port", "27017")
        database = self.config.get("database", "opsdroid")
        user = self.config.get("user")
        pwd = self.config.get("password")
        if user and pwd:
            path = "mongodb://{user}:{pwd}@{host}:{port}".format(
                user=user, pwd=pwd, host=host, port=port
            )
        else:
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
        if isinstance(data, str):
            data = {"value": data}
        if "_id" not in data:
            data["_id"] = key

        response = await self.database[self.collection].update_one(
            {"_id": data["_id"]}, {"$set": data}
        )
        if response.raw_result["updatedExisting"]:
            return

        await self.database[self.collection].insert_one(data)

    async def get(self, key):
        """Get a document from the database (key).

        Args:
            key (str): the key is the database name.

        """
        _LOGGER.debug("Getting %s from MongoDB.", key)
        response = await self.database[self.collection].find_one(
            {"$query": {"_id": key}, "$orderby": {"$natural": -1}}
        )
        if response.keys() == {"_id", "value"}:
            response = response["value"]
        return response

    async def delete(self, key):
        """Delete a document from the database (key).

        Args:
            key (str): the key is the database name.

        """
        _LOGGER.debug("Deleting %s from MongoDB.", key)
        return await self.database[self.collection].delete_one({"_id": key})
