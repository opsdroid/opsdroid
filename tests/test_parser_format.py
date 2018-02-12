
import asynctest
import asynctest.mock as amock

from opsdroid.core import OpsDroid
from opsdroid.matchers import match_parse
from opsdroid.message import Message
from opsdroid.parsers.parseformat import parse_format


class TestParserRegex(asynctest.TestCase):
    """Test the opsdroid regex parser."""

    async def test_parse_format(self):
        with OpsDroid() as opsdroid:
            mock_skill = amock.CoroutineMock()
            match_parse("Hello {name}")(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message("Hello world", "user", "default", mock_connector)

            skills = await parse_format(opsdroid, message)
            self.assertEqual(mock_skill, skills[0]["skill"])
            self.assertEqual(message.parse_result['name'], 'world')
