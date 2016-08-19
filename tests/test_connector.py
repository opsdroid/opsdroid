
import unittest

from opsdroid.connector import Connector


class TestConnectorBaseClass(unittest.TestCase):
    """Test the opsdroid connector base class."""

    def test_init(self):
        config = {"example_item": "test"}
        connector = Connector(config)
        self.assertEqual("", connector.name)
        self.assertEqual("test", connector.config["example_item"])

    def test_connect(self):
        connector = Connector({})
        with self.assertRaises(NotImplementedError):
            connector.connect({})

    def test_respond(self):
        connector = Connector({})
        with self.assertRaises(NotImplementedError):
            connector.respond({})
