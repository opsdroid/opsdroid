
import unittest
import logging
import sys
import unittest.mock as mock

sys.modules['subprocess'] = mock.MagicMock()

from opsdroid import helper  # noqa: E402


class TestHelper(unittest.TestCase):
    """Test the opsdroid helper classes."""

    def test_build_module_path(self):
        self.assertIn("test.test", helper.build_module_path("test", "test"))

    def test_set_logging_level(self):
        helper.set_logging_level('debug')
        self.assertEqual(10, logging.getLogger().getEffectiveLevel())

        helper.set_logging_level('info')
        self.assertEqual(20, logging.getLogger().getEffectiveLevel())

        helper.set_logging_level('warning')
        self.assertEqual(30, logging.getLogger().getEffectiveLevel())

        helper.set_logging_level('error')
        self.assertEqual(40, logging.getLogger().getEffectiveLevel())

        helper.set_logging_level('critical')
        self.assertEqual(50, logging.getLogger().getEffectiveLevel())

    def test_match(self):
        match = helper.match(r".*", "test")
        self.assertEqual(match.group(0), "test")

        match = helper.match(r"hello (.*)", "hello world")
        self.assertEqual(match.group(1), "world")

    def test_git_clone(self):
        helper.git_clone("https://github.com/rmccue/test-repository.git",
                         "/tmp/test", "master")
        self.assertEqual(len(sys.modules['subprocess'].mock_calls), 2)
