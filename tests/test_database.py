import unittest
import asynctest

from opsdroid.database import Database


class TestDatabaseBaseClass(unittest.TestCase):
    """Test the opsdroid database base class."""

    def test_init(self):
        config = {"example_item": "test"}
        database = Database(config)
        self.assertEqual("", database.name)
        self.assertEqual("test", database.config["example_item"])


class TestDatabaseBaseClassAsync(asynctest.TestCase):
    """Test the opsdroid database base class."""

    async def test_connect(self):
        database = Database({})
        with self.assertRaises(NotImplementedError):
            await database.connect()

    async def test_disconnect(self):
        database = Database({})
        try:
            await database.disconnect()
        except NotImplementedError:
            self.fail("disconnect() raised NotImplementedError unexpectedly!")

    async def test_get(self):
        database = Database({})
        with self.assertRaises(NotImplementedError):
            await database.get("test")

    async def test_put(self):
        database = Database({})
        with self.assertRaises(NotImplementedError):
            await database.put("test", {})

    async def test_delete(self):
        database = Database({})
        with self.assertRaises(NotImplementedError):
            await database.delete("test")
