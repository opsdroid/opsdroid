from unittest.mock import Mock

import asynctest
import asynctest.mock as amock

from opsdroid.__main__ import configure_lang
from opsdroid.core import OpsDroid
from opsdroid.matchers import match_event
from opsdroid import events
from opsdroid.parsers.event_type import parse_event_type


class TestParserEvent(asynctest.TestCase):
    """Test the opsdroid event parser."""

    async def setup(self):
        configure_lang({})

    async def getMockSkill(self):
        async def mockedskill(opsdroid, config, message):
            pass

        mockedskill.config = {}
        return mockedskill

    async def test_parse_message(self):
        with OpsDroid() as opsdroid:
            opsdroid.run_skill = amock.CoroutineMock()
            mock_skill = await self.getMockSkill()
            opsdroid.skills.append(match_event(events.Message)(mock_skill))

            mock_connector = amock.CoroutineMock()
            message = events.Message("Hello World", "user", "default", mock_connector)

            await opsdroid.parse(message)
            self.assertTrue(opsdroid.run_skill.called)

    async def test_parse_str_event(self):
        with OpsDroid() as opsdroid:
            opsdroid.run_skill = amock.CoroutineMock()
            mock_skill = await self.getMockSkill()
            opsdroid.skills.append(match_event("Message")(mock_skill))

            mock_connector = amock.CoroutineMock()
            message = events.Message("Hello World", "user", "default", mock_connector)

            await opsdroid.parse(message)
            self.assertTrue(opsdroid.run_skill.called)

    async def test_parse_invalid_str(self):
        with OpsDroid() as opsdroid:
            mock_skill = await self.getMockSkill()
            opsdroid.skills.append(match_event("Message2")(mock_skill))

            mock_connector = amock.CoroutineMock()
            message = events.Message("Hello World", "user", "default", mock_connector)

            with self.assertRaises(ValueError):
                await parse_event_type(opsdroid, message)
