
import asynctest
import asynctest.mock as amock

from opsdroid.core import OpsDroid
from opsdroid.matchers import match_always
from opsdroid.message import Message
from opsdroid.parsers.always import parse_always


class TestParserAlways(asynctest.TestCase):
    """Test the opsdroid always parser."""

    async def test_parse_always_decorator_parens(self):
        with OpsDroid() as opsdroid:
            mock_skill = amock.CoroutineMock()
            match_always()(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message("Hello world", "user", "default", mock_connector)

            await parse_always(opsdroid, message)

            self.assertTrue(mock_skill.called)

    async def test_parse_always_decorate_no_parens(self):
        with OpsDroid() as opsdroid:
            mock_skill = amock.CoroutineMock()
            match_always(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message("Hello world", "user", "default", mock_connector)

            await parse_always(opsdroid, message)

            self.assertTrue(mock_skill.called)

    async def test_parse_always_raises(self):
        with OpsDroid() as opsdroid:
            mock_skill = amock.CoroutineMock()
            mock_skill.side_effect = Exception()
            opsdroid.loader.current_import_config = {
                "name": "mocked-skill"
            }
            match_always()(mock_skill)
            self.assertEqual(len(opsdroid.skills), 1)

            mock_connector = amock.MagicMock()
            mock_connector.respond = amock.CoroutineMock()
            message = Message("Hello world", "user",
                              "default", mock_connector)

            await parse_always(opsdroid, message)

            self.assertTrue(mock_skill.called)
