import asyncio
import datetime
import unittest

import asynctest
import asynctest.mock as amock

from contextlib import suppress
from opsdroid.database.redis import RedisDatabase
from opsdroid.__main__ import configure_lang


class MockRedisClient:
    execute = None


class TestRedisDatabase(unittest.TestCase):
    """Test the opsdroid Redis database class."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        configure_lang({})

    def test_init(self):
        """Test initialisation of database class.

        This method will test the initialisation of the database
        class. It will assert if the database class properties are
        declared and equated to None.

        """
        database = RedisDatabase({})
        self.assertEqual(None, database.client)
        self.assertEqual(0, database.database)
        self.assertEqual("localhost", database.host)
        self.assertEqual(6379, database.port)
        self.assertEqual(None, database.password)

    def test_other(self):
        unserialized_data = {
            "example_string": "test",
            "example_datetime": datetime.datetime.utcfromtimestamp(1538389815),
            "example_date": datetime.date.fromtimestamp(1538366400),
        }

        serialized_data = RedisDatabase.convert_object_to_timestamp(unserialized_data)

        self.assertEqual(serialized_data["example_string"], "test")
        # Typically I would do assertDictEqual on the result, but as datetime are parsed based on the
        # timezone of the computer it makes the unittest fragile depending on the timezone of the user.
        self.assertEqual(serialized_data["example_datetime"][0:10], "datetime::")
        self.assertEqual(serialized_data["example_date"][0:6], "date::")

    def test_convert_timestamp_to_object(self):
        serialized_data = {
            "example_date": "date::1538366400",
            "example_datetime": "datetime::1538389815",
            "example_string": "test"
        }

        unserialized_data = RedisDatabase.convert_timestamp_to_object(serialized_data)

        self.assertEqual(unserialized_data["example_string"], "test")
        # Typically I would do assertDictEqual on the result, but as datetime are parsed based on the
        # timezone of the computer it makes the unittest fragile depending on the timezone of the user.
        self.assertIsInstance(unserialized_data["example_datetime"], datetime.datetime)
        self.assertIsInstance(unserialized_data["example_date"], datetime.date)


class TestRedisDatabaseAsync(asynctest.TestCase):
    """Test the opsdroid Redis Database class."""

    async def test_connect(self):
        opsdroid = amock.CoroutineMock()
        database = RedisDatabase({}, opsdroid=opsdroid)
        database.client = amock.CoroutineMock()
        database.client.Connection = amock.CoroutineMock()
        database.client.Connection.create = amock.CoroutineMock()

        await database.connect()

        with suppress(AttributeError):
            self.assertTrue(database.client.Connection.create.called)

    async def test_get(self):
        db = RedisDatabase({})
        db.client = MockRedisClient()
        db.client.get = amock.CoroutineMock(return_value='{"key":"value"}')

        result = await db.get("string")

        self.assertDictEqual(result, dict(key="value"))

    async def test_get_return_None(self):
        db = RedisDatabase({})
        db.client = MockRedisClient()
        db.client.get = amock.CoroutineMock(return_value=None)

        result = await db.get("string")

        self.assertEqual(result, None)

    async def test_put(self):
        db = RedisDatabase({})
        db.client = MockRedisClient()
        db.client.set = amock.CoroutineMock(return_value='{"key":"value"}')

        result = await db.put("string", dict(key="value"))

    async def test_disconnect(self):
        db = RedisDatabase({})
        db.client = MockRedisClient()
        db.client.close = amock.CoroutineMock()

        result = await db.disconnect()

        self.assertTrue(db.client.close.called)

