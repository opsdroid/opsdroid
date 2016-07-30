
import sys
import unittest
import unittest.mock as mock

sys.modules['opsdroid.core'] = mock.MagicMock()

from opsdroid import skills  # noqa: E402


class TestSkillDecorators(unittest.TestCase):
    """Test the opsdroid skills decorators."""

    def test_match_regex(self):
        sys.modules['opsdroid.core'].OpsDroid.instances = [mock.MagicMock()]
        self.assertEqual(
            len(sys.modules['opsdroid.core'].OpsDroid.instances), 1)
        matcher = skills.match_regex(r"(.*)")
        matcher(mock.MagicMock())
        self.assertEqual(
            len(sys.modules['opsdroid.core'].OpsDroid.instances[0].mock_calls),
            1)
