
import unittest
import unittest.mock as mock

from opsdroid.core import OpsDroid
from opsdroid import skills


class TestSkillDecorators(unittest.TestCase):
    """Test the opsdroid skills decorators."""

    def test_match_regex(self):
        with OpsDroid() as opsdroid:
            regex = r"(.*)"
            decorator = skills.match_regex(regex)
            mockedskill = mock.MagicMock()
            decorator(mockedskill)
            self.assertEqual(len(opsdroid.skills), 1)
            self.assertEqual(opsdroid.skills[0]["regex"], regex)
            self.assertIsInstance(opsdroid.skills[0]["skill"], mock.MagicMock)
