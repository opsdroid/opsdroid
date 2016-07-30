
import unittest
from opsdroid import helper


class TestHelper(unittest.TestCase):
    """Test the opsdroid helper classes."""

    def test_build_module_path(self):
        self.assertIn("test.test", helper.build_module_path("test", "test"))
