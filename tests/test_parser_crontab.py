import asynctest
import asynctest.mock as amock

from opsdroid.cli.start import configure_lang
from opsdroid.core import OpsDroid
from opsdroid.matchers import match_crontab
from opsdroid.parsers.crontab import parse_crontab


class TestParserCrontab(asynctest.TestCase):
    """Test the opsdroid crontab parser."""

    not_first_run_flag = True

    async def setup(self):
        configure_lang({})

    async def getMockSkill(self):
        async def mockedskill(opsdroid, config, message):
            pass

        mockedskill.config = {}
        return mockedskill

    async def getRaisingMockSkill(self):
        async def mockedskill(opsdroid, config, message):
            raise Exception()

        mockedskill.config = {}
        return mockedskill

    def true_once(self):
        if self.not_first_run_flag:
            self.not_first_run_flag = False
            return True
        else:
            return False

    async def test_parse_crontab(self):
        with OpsDroid() as opsdroid:
            self.not_first_run_flag = True
            opsdroid.eventloop.is_running = self.true_once
            opsdroid.run_skill = amock.CoroutineMock()
            with amock.patch("asyncio.sleep"):
                mock_skill = await self.getMockSkill()
                mock_skill.config = {"name": "greetings"}
                opsdroid.skills.append(match_crontab("* * * * *")(mock_skill))

                await parse_crontab(opsdroid)
                self.assertTrue(opsdroid.run_skill.called)

    async def test_parse_crontab_timezone(self):
        with OpsDroid() as opsdroid:
            self.not_first_run_flag = True
            opsdroid.eventloop.is_running = self.true_once
            opsdroid.run_skill = amock.CoroutineMock()
            with amock.patch("asyncio.sleep"):
                mock_skill = await self.getMockSkill()
                mock_skill.config = {"name": "greetings"}
                opsdroid.skills.append(
                    match_crontab("* * * * *", timezone="Europe/London")(mock_skill)
                )

                await parse_crontab(opsdroid)
                self.assertTrue(opsdroid.run_skill.called)

    async def test_parse_crontab_raises(self):
        with OpsDroid() as opsdroid:
            self.not_first_run_flag = True
            opsdroid.eventloop.is_running = self.true_once
            with amock.patch("asyncio.sleep"):
                mock_skill = await self.getRaisingMockSkill()
                mock_skill.config = {"name": "greetings"}
                opsdroid.skills.append(match_crontab("* * * * *")(mock_skill))
                self.assertEqual(len(opsdroid.skills), 1)

                await parse_crontab(opsdroid)
                self.assertLogs("_LOGGER", "exception")
