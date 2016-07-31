
import sys
import unittest
import unittest.mock as mock

sys.modules['sys'].exit = mock.MagicMock()

from opsdroid.core import OpsDroid  # noqa: E402
from opsdroid.message import Message  # noqa: E402


class TestCore(unittest.TestCase):
    """Test the opsdroid core class."""

    def test_core(self):
        with OpsDroid() as opsdroid:
            self.assertIsInstance(opsdroid, OpsDroid)

    def test_exit(self):
        with OpsDroid() as opsdroid:
            sys.modules['sys'].exit.mock_calls = []
            opsdroid.exit()
            self.assertEqual(len(sys.modules['sys'].exit.mock_calls), 1)

    def test_critical(self):
        with OpsDroid() as opsdroid:
            sys.modules['sys'].exit.mock_calls = []
            opsdroid.critical("An error", 1)
            self.assertEqual(len(sys.modules['sys'].exit.mock_calls), 1)

    def test_load_regex_skill(self):
        with OpsDroid() as opsdroid:
            regex = r".*"
            skill = mock.MagicMock()
            opsdroid.load_regex_skill(regex, skill)
            self.assertEqual(len(opsdroid.skills), 1)
            self.assertEqual(opsdroid.skills[0]["regex"], regex)
            self.assertIsInstance(opsdroid.skills[0]["skill"], mock.MagicMock)

    def test_parse(self):
        with OpsDroid() as opsdroid:
            regex = r".*"
            skill = mock.MagicMock()
            mock_connector = mock.MagicMock()
            opsdroid.load_regex_skill(regex, skill)
            message = Message("Hello world", "user", "default", mock_connector)
            opsdroid.parse(message)
            self.assertEqual(len(skill.mock_calls), 1)
