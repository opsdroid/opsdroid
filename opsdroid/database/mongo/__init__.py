# -*- coding: utf-8 -*-
"""A module for opsdroid to allow persist in mongo database."""
import logging
from motor.motor_asyncio import AsyncIOMotorClient

from opsdroid.database import Database


class DatabaseMongo(Database):
    """A module for opsdroid to allow memory to persist in a mongo database.

    Attributes:

    """

    def __init__(self, config, opsdroid=None):
        """Create the connection.

        Set some basic properties from the database config such as the name
        of this database.

        Args:
            config (dict): The config for this database specified in the
                           `configuration.yaml` file.

        """
        super().__init__(config, opsdroid=opsdroid)
        logging.debug("Loaded mongo database connector")
        self.name = "mongo"
        self.config = config
        self.client = None
        self.database = None

    async def connect(self):
        """Connect to the database."""
        host = self.config["host"] if "host" in self.config else "localhost"
        port = self.config["port"] if "port" in self.config else "27017"
        database = self.config["database"] \
            if "database" in self.config else "opsdroid"
        path = "mongodb://" + host + ":" + port
        self.client = AsyncIOMotorClient(path)
        self.database = self.client[database]
        logging.info("Connected to mongo")

    async def put(self, key, data):
        """Insert or replace an object into the database for a given key.

        Args:
            key (str): the key is the databasename
            data (object): the data to be inserted or replaced
        """
        logging.debug("Putting %s into mongo", key)
        if "_id" in data:
            await self.database[key].update_one({"_id": data["_id"]},
                                                {"$set": data})
        else:
            await self.database[key].insert_one(data)

    async def get(self, key):
        """Get a document from the database (key).

        Args:
            key (str): the key is the databasename.
        """
        logging.debug("Getting %s from mongo", key)
        return await self.database[key].find_one(
            {"$query": {}, "$orderby": {"$natural": -1}}
            )
