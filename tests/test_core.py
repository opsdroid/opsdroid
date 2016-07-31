
import unittest

from opsdroid.core import OpsDroid


class TestCore(unittest.TestCase):
    """Test the opsdroid core class."""

    def setup(self):
        return OpsDroid()

    def test_core(self):
        opsdroid = self.setup()
        self.assertIsInstance(opsdroid, OpsDroid)
