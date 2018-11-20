"""Tests for the DatabaseSqlite class."""
import asyncio
import json
import datetime

import unittest
import unittest.mock as mock
import asynctest
import asynctest.mock as amock

from opsdroid.database.sqlite import DatabaseSqlite, JSONEncoder, JSONDecoder
from opsdroid.database.sqlite import register_json_type
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
        self.assertEqual({'isolation_level': None}, database.conn_args)


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
            await database.connect(opsdroid)
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
            await database.connect(opsdroid)
            await database.put("hello", {})
            data = await database.get("hello")
        except NotImplementedError:
            raise Exception
        else:
            self.assertEqual("opsdroid", database.table)
            self.assertEqual({}, data)
            self.assertEqual("Connection", type(database.client).__name__)


class TestJSONEncoder(unittest.TestCase):
    """A JSON Encoder test class.

    Test the custom json encoder class.

    """

    def setUp(self):
        self.loop = asyncio.new_event_loop()

    def test_datetime_to_dict(self):
        """Test default of json encoder class.

        This method will test the conversion of the datetime
        object to dict.

        """
        type_cls = datetime.datetime
        test_obj = datetime.datetime(2018, 10, 2, 0, 41, 17, 74644)
        encoder = JSONEncoder()
        obj = encoder.default(o=test_obj)
        self.assertEqual({
            "__class__": type_cls.__name__,
            "year": 2018,
            "month": 10,
            "day": 2,
            "hour": 0,
            "minute": 41,
            "second": 17,
            "microsecond": 74644
        }, obj)


class TestJSONDecoder(unittest.TestCase):
    """A JSON Decoder test class.

    Test the custom json decoder class.

    """

    def setUp(self):
        self.loop = asyncio.new_event_loop()

    def test_dict_to_datetime(self):
        """Test call of json decoder class.

        This method will test the conversion of the dict to
        datetime object.

        """
        test_obj = {
            "__class__": datetime.datetime.__name__,
            "year": 2018,
            "month": 10,
            "day": 2,
            "hour": 0,
            "minute": 41,
            "second": 17,
            "microsecond": 74644
        }
        decoder = JSONDecoder()
        obj = decoder(test_obj)
        self.assertEqual(datetime.datetime(2018, 10, 2, 0, 41, 17, 74644), obj)
