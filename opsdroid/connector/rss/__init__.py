"""A connector which checks RSS feeds for items."""
import asyncio
import logging
import time

import aiohttp
import atoma

from opsdroid.connector import Connector
from opsdroid.connector.rss.events import FeedItemEvent

_LOGGER = logging.getLogger(__name__)


class ConnectorRSS(Connector):
    """A connector to trigger events from feed items."""

    def __init__(self, config, opsdroid=None):
        """Create the connector."""
        super().__init__(config, opsdroid=opsdroid)
        self.name = self.config.get("name", "rss")
        self._feeds = {}
        self.running = False
        self._poll_time = 5  # Shortest polling interval is 5 seconds

    async def connect(self):
        """Get all feed urls from skills with the match_rss decorator."""
        for skill in self.opsdroid.skills:
            for matcher in skill.matchers:
                if "feed_url" in matcher:
                    feed = matcher.copy()
                    if feed["feed_url"] not in self._feeds:
                        feed["last_checked"] = time.time()
                        feed["feed"] = await self._update_feed(feed["feed_url"])
                        self._feeds[feed["feed_url"]] = feed
                    else:
                        # If feed is already added check for a shorter interval and
                        # reduce it if necessary
                        if feed["interval"] < self._feeds[feed["feed_url"]]["interval"]:
                            self._feeds[feed["feed_url"]]["interval"] = feed["interval"]
        self.running = True

    async def disconnect(self):
        """Disconnect and reset feed urls."""
        self._feeds = {}
        self.running = False

    async def _get_feeds(self):
        await asyncio.sleep(self._poll_time)
        for feed_url, feed in self._feeds.items():
            if time.time() > feed["last_checked"] + feed["interval"]:
                newfeed = await self._update_feed(feed["feed_url"])
                new_items = await self._check_for_new_items(newfeed, feed["feed"])
                if new_items:
                    await self._run_skills(feed_url, new_items)
                feed["feed"] = newfeed

    async def listen(self):
        """Listen method of the connector."""
        while self.running:
            await self._get_feeds()

    async def _run_skills(self, feed_url, new_items):
        """Run relevant skills for each new item found in feed."""
        for item in new_items:
            for skill in self.opsdroid.skills:
                for matcher in skill.matchers:
                    if "feed_url" in matcher and matcher["feed_url"] == feed_url:
                        # We shouldn't be doing this here. We should hand off to opsdroid.parse()
                        # but there isn't a clean place to put this logic in there yet. Once we
                        # start on really hashing out #933 this should move somewhere else.
                        self.opsdroid.eventloop.create_task(
                            self.opsdroid.run_skill(
                                skill,
                                skill.config,
                                FeedItemEvent(
                                    item=item,
                                    target=feed_url,
                                    connector=self,
                                    raw_event=item,
                                ),
                            )
                        )

    @staticmethod
    async def _check_for_new_items(newfeed, oldfeed):
        """Check the diff between two feeds and return new items."""
        new_items = []
        if isinstance(newfeed, atoma.rss.RSSChannel):
            for item in newfeed.items:
                if item not in oldfeed.items:
                    new_items.append(item)
        else:
            for item in newfeed.entries:
                if item not in oldfeed.entries:
                    new_items.append(item)
        return new_items

    @staticmethod
    async def _update_feed(feed):
        """Get the contents of a feed."""
        async with aiohttp.ClientSession() as session:
            async with session.get(feed) as resp:
                if "atom" in resp.content_type:
                    return atoma.parse_atom_bytes(await resp.read())
                elif "rss" in resp.content_type:
                    return atoma.parse_rss_bytes(await resp.read())
                else:
                    _LOGGER.error(
                        "Feed type %s not supported for feed %s.",
                        resp.content_type,
                        feed,
                    )
                    return None
