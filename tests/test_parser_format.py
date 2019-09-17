import asynctest
import asynctest.mock as amock

from opsdroid.__main__ import configure_lang
from opsdroid.core import OpsDroid
from opsdroid.matchers import match_parse
from opsdroid.events import Message
from opsdroid.parsers.parseformat import parse_format


class TestParserParseFormat(asynctest.TestCase):
    """Test the opsdroid parse_format parser."""

    async def setup(self):
        configure_lang({})

    async def getMockSkill(self):
        async def mockedskill(opsdroid, config, message):
            pass

        mockedskill.config = {}
        return mockedskill

    async def test_parse_format_match_condition(self):
        with OpsDroid() as opsdroid:
            mock_skill = await self.getMockSkill()
            opsdroid.skills.append(match_parse("Hello")(mock_skill))

            mock_connector = amock.CoroutineMock()

            message = Message("Hello world", "user", "default", mock_connector)
            skills = await parse_format(opsdroid, opsdroid.skills, message)
            self.assertEqual(len(skills), 0)

            message = Message("Hello", "user", "default", mock_connector)
            skills = await parse_format(opsdroid, opsdroid.skills, message)
            self.assertEqual(mock_skill, skills[0]["skill"])
            assert skills[0]["message"] is message
            # test that the original object has had a new attribute added
            assert hasattr(message, "parse_result")

    async def test_parse_format_search_condition(self):
        with OpsDroid() as opsdroid:
            mock_skill = await self.getMockSkill()
            opsdroid.skills.append(
                match_parse("Hello", matching_condition="search")(mock_skill)
            )

            mock_connector = amock.CoroutineMock()

            message = Message("Hello", "user", "default", mock_connector)
            skills = await parse_format(opsdroid, opsdroid.skills, message)
            self.assertEqual(mock_skill, skills[0]["skill"])

            message = Message("Hello world", "user", "default", mock_connector)
            skills = await parse_format(opsdroid, opsdroid.skills, message)
            self.assertEqual(mock_skill, skills[0]["skill"])

    async def test_parse_format_parameters(self):
        with OpsDroid() as opsdroid:
            mock_skill = await self.getMockSkill()
            opsdroid.skills.append(
                match_parse("say {text} {num:d} times", case_sensitive=False)(
                    mock_skill
                )
            )

            mock_connector = amock.CoroutineMock()
            message = Message("Say hello 42 times", "user", "default", mock_connector)

            skills = await parse_format(opsdroid, opsdroid.skills, message)
            self.assertEqual(mock_skill, skills[0]["skill"])

            parsed_message = skills[0]["message"]
            self.assertEqual(parsed_message.parse_result["text"], "hello")
            self.assertEqual(parsed_message.parse_result["num"], 42)

            self.assertEqual(len(parsed_message.entities.keys()), 2)
            self.assertTrue("text" in parsed_message.entities.keys())
            self.assertEqual(parsed_message.entities["text"]["value"], "hello")
