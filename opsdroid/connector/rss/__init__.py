"""A connector which checks RSS feeds for items."""
import logging
import time

import aiohttp
import arrow
import atoma

from opsdroid.connector import Connector
from opsdroid.connector.rss.events import FeedItemEvent

_LOGGER = logging.getLogger(__name__)


class ConnectorRSS(Connector):
    def __init__(self, config, opsdroid=None):
        """Create the connector."""
        super().__init__(config, opsdroid=opsdroid)
        self.feeds = {}

    async def connect(self):
        for skill in opsdroid.skills:
            for matcher in skill.matchers:
                if "feed_url" in matcher:
                    feed = matcher
                    if feed["feed_url"] not in self.feeds:
                        feed["last_checked"] = time.time()
                        feed["feed"] = self.update_feed(feed["feed_url"])
                        self.feeds[feed["feed_url"]] = feed
                    else:
                        # If feed is already added check for a shorter interval and
                        # reduce it if necessary
                        if feed["interval"] < self.feeds[feed["feed_url"]]:
                            self.feeds[feed["feed_url"]]["interval"] = feed["interval"]

    async def disconnect(self):
        self.feeds = {}

    async def listen(self):
        await asyncio.sleep(60 - arrow.now().time().second)
        for feed_url, feed in self.feeds:
            if time.time() > feed["last_checked"] + feed["interval"]:
                newfeed = self.update_feed(feed["feed_url"])
                self.check_for_new_items(newfeed, feed["feed"])
                feed["feed"] = newfeed

    async def check_for_new_items(newfeed, oldfeed):
        # TODO Diff the feeds and emit events for items that are in new but not old
        if False:
            await self.opsdroid.parse(
                FeedItemEvent(
                    message["text"],
                    user_info["name"],
                    message["channel"],
                    self,
                    raw_event=message,
                )
            )

    @staticmethod
    async def update_feed(feed):
        async with aiohttp.ClientSession() as session:
            async with session.get(feed) as resp:
                if "atom" in resp.content_type:
                    return atoma.parse_atom_bytes(await response.read())
                elif "rss" in resp.content_type:
                    return atoma.parse_rss_bytes(await response.read())
                else:
                    _LOGGER.error(
                        "Feed type %s not supported for feed %s.",
                        resp.content_type,
                        feed,
                    )
