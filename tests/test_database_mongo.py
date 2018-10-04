"""Tests for the DatabaseMongo class. """

import unittest
import asynctest


from opsdroid.database.mongo import DatabaseMongo
from mockmodules.databases.mongo.mongo_database import DatabaseMongoTest

class TestDatabaseMongoClass(unittest.TestCase):
    """Test the opsdroid mongo database class."""

    def test_init(self):
        """Initialization fo mock database"""
        config = {"example_item": "test"}
        database = DatabaseMongo(config)
        self.assertEqual("mongo", database.name)
        self.assertEqual("test", database.config["example_item"])


class TestDatabaseBaseMongoClassAsync(asynctest.TestCase):
    """Test the opsdroid database base class."""

    async def test_connect(self):
        """test the method connect"""
        database = DatabaseMongoTest({})
        try:
            await database.connect({})
        except NotImplementedError:
            raise Exception
        else:
            pass

    async def test_get(self):
        """test of mocked method get"""
        database = DatabaseMongoTest({})
        try:
            await database.get("test")
        except NotImplementedError:
            raise Exception
        else:
            pass

    async def test_get2(self):
        """test of mocked method get"""
        database = DatabaseMongo({})
        try:
            await database.get("test")
        except TypeError:
            pass
        else:
            raise Exception

    async def test_put(self):
        """test of mocked method put"""
        database = DatabaseMongoTest({})
        try:
            await database.put("test", "value")
        except NotImplementedError:
            raise Exception
        else:
            pass

    async def test_put2(self):
        """test of mocked method put"""
        database = DatabaseMongo({})
        try:
            await database.put("test", "value")
        except TypeError:
            pass
        else:
            raise Exception
