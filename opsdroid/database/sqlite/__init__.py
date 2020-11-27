"""A module for sqlite database."""
import os
import logging
import json
import aiosqlite

from opsdroid.const import DEFAULT_ROOT_PATH
from opsdroid.database import Database
from opsdroid.helper import JSONEncoder, JSONDecoder

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = {"path": str, "file": str, "table": str}

# pylint: disable=too-few-public-methods
# As the current module needs only one public method to register json types


class DatabaseSqlite(Database):
    """A sqlite database class.

    SQLite Database class used to persist data in sqlite.

    """

    def __init__(self, config, opsdroid=None):
        """Initialise the sqlite database.

        Set basic properties of the database. Initialise properties like
        name, connection arguments, database file, table name and config.

        Args:
            config (dict): The configuration of the database which consists
                           of `file` and `table` name of the sqlite database
                           specified in `configuration.yaml` file.
            opsdroid (OpsDroid): An instance of opsdroid.core.

        """
        super().__init__(config, opsdroid=opsdroid)
        self.name = "sqlite"
        self.config = config
        self.conn_args = {"isolation_level": None}
        if "file" in self.config:
            self.db_file = self.config["file"]
            _LOGGER.warning(
                "The option 'file' is deprecated, please use 'path' instead."
            )
        else:
            self.db_file = self.config.get(
                "path", os.path.join(DEFAULT_ROOT_PATH, "sqlite.db")
            )
        self.table = self.config.get("table", "opsdroid")
        _LOGGER.debug(_("Loaded sqlite database connector"))

    async def connect(self):
        """Connect to the database.

        This method will connect to the sqlite database. It will create
        the database file named `sqlite.db` in DEFAULT_ROOT_PATH and set
        the table name to `opsdroid`. It will create the table if it does
        not exist in the database.

        Args:
            opsdroid (OpsDroid): An instance of opsdroid core.

        """
        self.client = await aiosqlite.connect(self.db_file, **self.conn_args)

        cur = await self.client.cursor()
        await cur.execute(
            "CREATE TABLE IF NOT EXISTS {}"
            "(key text PRIMARY KEY, data text)".format(self.table)
        )
        await self.client.commit()

        _LOGGER.info(_("Connected to sqlite %s"), self.db_file)

    async def put(self, key, data):
        """Put data into the database.

        This method will insert or replace an object into the database for
        a given key. The data object is serialised into JSON data using the
        JSONEncoder class.

        Args:
            key (string): The key to store the data object under.
            data (object): The data object to store.

        """
        _LOGGER.debug(_("Putting %s into sqlite"), key)
        json_data = json.dumps(data, cls=JSONEncoder)

        cur = await self.client.cursor()
        await cur.execute("DELETE FROM {} WHERE key=?".format(self.table), (key,))
        await cur.execute(
            "INSERT INTO {} VALUES (?, ?)".format(self.table), (key, json_data)
        )
        await self.client.commit()

    async def get(self, key):
        """Get data from the database for a given key.

        Args:
            key (string): The key to lookup in the database.

        Returns:
            object or None: The data object stored for that key, or None if no
                            object found for that key.

        """
        _LOGGER.debug(_("Getting %s from sqlite"), key)
        data = None

        cur = await self.client.cursor()
        await cur.execute("SELECT data FROM {} WHERE key=?".format(self.table), (key,))
        row = await cur.fetchone()
        if row:
            data = json.loads(row[0], object_hook=JSONDecoder())

        return data

    async def delete(self, key):
        """Delete data from the database for a given key.

        Args:
            key (string): The key to delete in the database.

        """
        _LOGGER.debug(_("Deleting %s from sqlite"), key)

        cur = await self.client.cursor()
        await cur.execute("DELETE FROM {} WHERE key=?".format(self.table), (key,))
        await self.client.commit()

    async def disconnect(self):
        """Disconnect from the database."""
        if self.client:
            await self.client.close()
