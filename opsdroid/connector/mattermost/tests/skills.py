from opsdroid.skill import Skill
from opsdroid.matchers import match_regex
import logging

_LOGGER = logging.getLogger(__name__)


class HelloSkill(Skill):
    @match_regex(r"^.*Unit Test Message$")
    async def hello(self, message):
        _LOGGER.info("Message arrived in Unit Test skill: '%s'", message.text)
