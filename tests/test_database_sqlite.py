"""Tests for the DatabaseSqlite class."""
import asyncio

import unittest
import asynctest
import asynctest.mock as amock

from opsdroid.database.sqlite import DatabaseSqlite
from opsdroid.__main__ import configure_lang


class TestDatabaseSqlite(unittest.TestCase):
    """A database test class.

    Test the opsdroid sqlite database class.

    """

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        configure_lang({})

    def test_init(self):
        """Test initialisation of database class.

        This method will test the initialisation of the database
        class. It will assert if the database class properties are
        declared and equated to None.

        """
        database = DatabaseSqlite({"file": "sqlite.db"})
        self.assertEqual(None, database.client)
        self.assertEqual(None, database.database)
        self.assertEqual(None, database.db_file)
        self.assertEqual(None, database.table)
        self.assertEqual({"isolation_level": None}, database.conn_args)


class TestDatabaseSqliteAsync(asynctest.TestCase):
    """A async database test class.

    Test the async methods of the opsdroid sqlite database class.

    """

    async def test_connect(self):
        """Test database connection.

        This method will test the database connection of sqlite database.
        As the database is created `opsdroid` table is created first.

        """
        database = DatabaseSqlite({"file": "sqlite.db"})
        opsdroid = amock.CoroutineMock()
        opsdroid.eventloop = self.loop

        try:
            await database.connect()
        except NotImplementedError:
            raise Exception
        else:
            self.assertEqual("opsdroid", database.table)
            self.assertEqual("Connection", type(database.client).__name__)

    async def test_get_and_put(self):
        """Test get and put functions of database

        This method will test the get and put functions which help to read
        and write data from the database. The function `put` a value with
        key and asserts the same value after the `get` operation is completed.

        """
        database = DatabaseSqlite({"file": "sqlite.db"})
        opsdroid = amock.CoroutineMock()
        opsdroid.eventloop = self.loop

        try:
            await database.connect()
            await database.put("hello", {})
            data = await database.get("hello")
        except NotImplementedError:
            raise Exception
        else:
            self.assertEqual("opsdroid", database.table)
            self.assertEqual({}, data)
            self.assertEqual("Connection", type(database.client).__name__)
