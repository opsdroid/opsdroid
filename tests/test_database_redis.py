import asyncio
import aioredis
import unittest

import asynctest
import asynctest.mock as amock

from contextlib import suppress
from opsdroid.database.redis import RedisDatabase
from opsdroid.cli.start import configure_lang


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
        self.assertLogs("_LOGGER", "debug")


class TestRedisDatabaseAsync(asynctest.TestCase):
    """Test the opsdroid Redis Database class."""

    async def test_connect(self):
        opsdroid = amock.CoroutineMock()
        database = RedisDatabase({}, opsdroid=opsdroid)

        with amock.patch.object(aioredis, "create_pool") as mocked_connection:
            mocked_connection.side_effect = NotImplementedError

            with suppress(NotImplementedError):
                await database.connect()
                self.assertTrue(mocked_connection.called)
                self.assertLogs("_LOGGER", "info")

    async def test_connect_failure(self):
        opsdroid = amock.CoroutineMock()
        database = RedisDatabase({}, opsdroid=opsdroid)

        with amock.patch.object(aioredis, "create_pool") as mocked_connection:
            mocked_connection.side_effect = OSError()

            with suppress(OSError):
                await database.connect()
                self.assertLogs("_LOGGER", "warning")

    async def test_connect_logging(self):
        opsdroid = amock.CoroutineMock()
        database = RedisDatabase({}, opsdroid=opsdroid)

        with amock.patch.object(aioredis, "create_pool") as mocked_connection:
            mocked_connection.set_result = amock.CoroutineMock()

            await database.connect()
            self.assertTrue(mocked_connection.called)
            self.assertLogs("_LOGGER", "info")

    async def test_get(self):
        db = RedisDatabase({})
        db.client = MockRedisClient()
        db.client.execute = amock.CoroutineMock(return_value='{"key":"value"}')

        result = await db.get("string")

        self.assertDictEqual(result, dict(key="value"))

    async def test_get_return_None(self):
        db = RedisDatabase({})
        db.client = MockRedisClient()
        db.client.execute = amock.CoroutineMock(return_value=None)

        result = await db.get("string")

        self.assertEqual(result, None)

    async def test_put(self):
        db = RedisDatabase({})
        db.client = MockRedisClient()
        db.client.execute = amock.CoroutineMock(return_value='{"key":"value"}')

        result = await db.put("string", dict(key="value"))

    async def test_disconnect(self):
        db = RedisDatabase({})
        db.client = MockRedisClient()
        db.client.close = amock.CoroutineMock()

        result = await db.disconnect()

        self.assertTrue(db.client.close.called)
