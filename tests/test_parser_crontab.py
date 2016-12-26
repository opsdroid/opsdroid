
import asynctest
import asynctest.mock as amock

from opsdroid.core import OpsDroid
from opsdroid.skills import match_crontab
from opsdroid.parsers.crontab import parse_crontab


class TestParserCrontab(asynctest.TestCase):
    """Test the opsdroid crontab parser."""

    not_first_run_flag = True

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
            with amock.patch('asyncio.sleep'):
                mock_skill = amock.CoroutineMock()
                match_crontab("* * * * *")(mock_skill)

                await parse_crontab(opsdroid)
                self.assertTrue(mock_skill.called)

    async def test_parse_crontab_raises(self):
        with OpsDroid() as opsdroid:
            self.not_first_run_flag = True
            opsdroid.eventloop.is_running = self.true_once
            with amock.patch('asyncio.sleep'):
                mock_skill = amock.CoroutineMock()
                mock_skill.side_effect = Exception()
                match_crontab("* * * * *")(mock_skill)
                self.assertEqual(len(opsdroid.skills), 1)

                await parse_crontab(opsdroid)
                self.assertTrue(mock_skill.called)
