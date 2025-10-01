from opsdroid.skill import Skill
from opsdroid.matchers import match_regex

class ByeSkill(Skill):

    @match_regex(r'bye')
    async def say_goodbye(self, message):
        await message.respond("Goodbye!")
