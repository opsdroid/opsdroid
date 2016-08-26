
import unittest

from opsdroid.database import Database


class TestDatabaseBaseClass(unittest.TestCase):
    """Test the opsdroid database base class."""

    def test_init(self):
        config = {"example_item": "test"}
        database = Database(config)
        self.assertEqual("", database.name)
        self.assertEqual("test", database.config["example_item"])

    def test_connect(self):
        database = Database({})
        with self.assertRaises(NotImplementedError):
            database.connect({})

    def test_get(self):
        database = Database({})
        with self.assertRaises(NotImplementedError):
            database.get("test")

    def test_put(self):
        database = Database({})
        with self.assertRaises(NotImplementedError):
            database.put("test", {})
