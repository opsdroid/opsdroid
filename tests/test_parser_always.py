import asynctest
import asynctest.mock as amock

from opsdroid.cli.start import configure_lang
from opsdroid.core import OpsDroid
from opsdroid.matchers import match_always
from opsdroid.events import Message
from opsdroid.parsers.always import parse_always


class TestParserAlways(asynctest.TestCase):
    """Test the opsdroid always parser."""

    async def setup(self):
        configure_lang({})

    async def getMockSkill(self):
        async def mockedskill(config, message):
            pass

        mockedskill.config = {}
        return mockedskill

    async def getRaisingMockSkill(self):
        async def mockedskill(config, message):
            raise Exception()

        mockedskill.config = {}
        return mockedskill

    async def test_parse_always_decorator_parens(self):
        with OpsDroid() as opsdroid:
            mock_skill = await self.getMockSkill()
            opsdroid.skills.append(match_always()(mock_skill))
            opsdroid.run_skill = amock.CoroutineMock()

            mock_connector = amock.CoroutineMock()
            message = Message(
                text="Hello world",
                user="user",
                target="default",
                connector=mock_connector,
            )

            await parse_always(opsdroid, message)

            self.assertTrue(opsdroid.run_skill.called)

    async def test_parse_always_decorate_no_parens(self):
        with OpsDroid() as opsdroid:
            mock_skill = await self.getMockSkill()
            opsdroid.skills.append(match_always(mock_skill))
            opsdroid.run_skill = amock.CoroutineMock()

            mock_connector = amock.CoroutineMock()
            message = Message(
                text="Hello world",
                user="user",
                target="default",
                connector=mock_connector,
            )

            await parse_always(opsdroid, message)

            self.assertTrue(opsdroid.run_skill.called)

    async def test_parse_always_raises(self):
        with OpsDroid() as opsdroid:
            mock_skill = await self.getRaisingMockSkill()
            mock_skill.config = {"name": "greetings"}
            opsdroid.skills.append(match_always()(mock_skill))
            self.assertEqual(len(opsdroid.skills), 1)

            mock_connector = amock.MagicMock()
            mock_connector.send = amock.CoroutineMock()
            message = Message(
                text="Hello world",
                user="user",
                target="default",
                connector=mock_connector,
            )

            await parse_always(opsdroid, message)
            self.assertLogs("_LOGGER", "exception")
