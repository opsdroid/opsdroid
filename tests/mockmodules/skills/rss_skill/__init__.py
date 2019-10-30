from opsdroid.skill import Skill
from opsdroid.matchers import match_rss


class TestSkill(Skill):
    def __init__(self, opsdroid, config, *args, **kwargs):
        super().__init__(opsdroid, config, *args, **kwargs)
        pass

    @match_rss("https://example.com/feed.rss")
    async def test(self, event):
        pass

    @match_rss("https://example.com/feed.rss", interval="5")
    async def test2(self, event):
        pass
