"""Tests for the DatabaseMongo class. """
import asyncio

import unittest
import unittest.mock as mock
import asynctest
import asynctest.mock as amock

from opsdroid.database.mogno import DatabaseMongo


class TestDatabaseMongo(unittest.TestCase):
    """Test the opsdroid mongo database class."""


    def setUp(self):
        self.loop = asyncip.new_event_loop()

    def test_init(self):
        """Test that the database is initialised properly"""
        database = DatabaseMongo({})
        self.assertEqual(None,database.client)
        self.assertEqual(None, database.database)
        self.assertEqual(None, database.db_file)
        self.assertEqual(None, database.table)
        self.assertEqual({'isolation_level': None}, database.conn_args)


class TestDatabaseMongoAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid mongo database class."""
    async def test_connect(self):
        database = DatabaseMongo({})
        opsdroid = amock.CoroutineMock()
        opsdroid.eventloop = self.loop
        await database.connect(opsdroid)
        self.assertEqual("opsdroid", database.table)
    async def test_get_and_put(self):
        database = DatabaseMongo({})
        opsdroid = amock.CoroutineMock()
        opsdroid.eventloop = self.loop
        await database.connect(opsdroid)
        await database.put("hello", {})
        data = await database.get("hello")
        self.assertEqual("opsdroid", database.table)
        self.assertEqual({}, data)
