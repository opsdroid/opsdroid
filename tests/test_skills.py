
import unittest
import unittest.mock as mock

from opsdroid.core import OpsDroid
from opsdroid import matchers


class TestSkillDecorators(unittest.TestCase):
    """Test the opsdroid skills decorators."""

    def test_match_regex(self):
        with OpsDroid() as opsdroid:
            regex = r"(.*)"
            mockedskill = mock.MagicMock()
            decorator = matchers.match_regex(regex)
            decorator(mockedskill)
            self.assertEqual(len(opsdroid.skills), 1)
            self.assertEqual(opsdroid.skills[0]["regex"], regex)
            self.assertIsInstance(opsdroid.skills[0]["skill"], mock.MagicMock)

    def test_match_apiai(self):
        with OpsDroid() as opsdroid:
            action = "myaction"
            mockedskill = mock.MagicMock()
            decorator = matchers.match_apiai_action(action)
            decorator(mockedskill)
            self.assertEqual(len(opsdroid.skills), 1)
            self.assertEqual(opsdroid.skills[0]["apiai_action"], action)
            self.assertIsInstance(opsdroid.skills[0]["skill"], mock.MagicMock)
            intent = "myIntent"
            decorator = matchers.match_apiai_intent(intent)
            decorator(mockedskill)
            self.assertEqual(len(opsdroid.skills), 2)
            self.assertEqual(opsdroid.skills[1]["apiai_intent"], intent)
            self.assertIsInstance(opsdroid.skills[1]["skill"], mock.MagicMock)

    def test_match_crontab(self):
        with OpsDroid() as opsdroid:
            crontab = "* * * * *"
            mockedskill = mock.MagicMock()
            decorator = matchers.match_crontab(crontab)
            decorator(mockedskill)
            self.assertEqual(len(opsdroid.skills), 1)
            self.assertEqual(opsdroid.skills[0]["crontab"], crontab)
            self.assertIsInstance(opsdroid.skills[0]["skill"], mock.MagicMock)
