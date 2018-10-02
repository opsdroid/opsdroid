import datetime
import time
import unittest

import aioredis
import asynctest
import asynctest.mock as amock

from opsdroid.database.redis import RedisDatabase


class MockRedisClient():
    execute = None


class TestRedisDatabase(unittest.TestCase):
    """Test the opsdroid Redis database class."""

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
        db = RedisDatabase({})
        db._connect = amock.CoroutineMock()
        await db.connect({})

        db._connect.assert_awaited_once()

    async def test_get(self):
        db = RedisDatabase({})
        db.client = MockRedisClient()
        db.client.execute = amock.CoroutineMock(return_value='{"key":"value"}')

        result = await db.get("string")

        self.assertDictEqual(result, dict(key="value"))
        db.client.execute.assert_awaited_once()

    async def test_put(self):
        db = RedisDatabase({})
        db.client = MockRedisClient()
        db.client.execute = amock.CoroutineMock(return_value='{"key":"value"}')

        result = await db.put("string", dict(key="value"))

        db.client.execute.assert_awaited_once()
