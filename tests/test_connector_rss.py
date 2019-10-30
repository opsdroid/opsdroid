"""Tests for the RocketChat class."""

import os.path

import asyncio
import unittest
import asynctest
import asynctest.mock as amock

from opsdroid.cli.start import configure_lang
from opsdroid.core import OpsDroid
from opsdroid.connector.rss import ConnectorRSS
from opsdroid.connector.rss.events import FeedItemEvent
from opsdroid.const import MODULE_ROOT

import atoma


class TestConnectorRSS(unittest.TestCase):
    """Test the opsdroid RSS connector class."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()

    def test_init(self):
        """Test that the connector is initialised properly."""
        connector = ConnectorRSS({"name": "rss"})
        self.assertEqual({}, connector._feeds)
        self.assertEqual("rss", connector.name)


class TestConnectorRSSAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid RSS connector class."""

    def setUp(self):
        configure_lang({})

    async def test_connect_disconnect(self):
        opsdroid = OpsDroid(
            config={
                "connectors": [{"name": "rss"}],
                "skills": [
                    {
                        "name": "test",
                        "no-cache": True,
                        "path": os.path.join(
                            MODULE_ROOT, "..", "tests/mockmodules/skills/rss_skill"
                        ),
                    }
                ],
            }
        )
        await opsdroid.load()
        connector = ConnectorRSS({"name": "rss"}, opsdroid=opsdroid)
        connector._update_feed = amock.CoroutineMock()

        await connector.connect()
        self.assertEqual(connector.running, True)
        self.assertTrue(connector._update_feed.awaited)
        self.assertEqual(len(connector._feeds), 1)
        self.assertEqual(list(connector._feeds.values())[0]["interval"], 5)

        await connector.disconnect()
        self.assertEqual(connector.running, False)
        self.assertEqual(len(connector._feeds), 0)

        await opsdroid.unload()

    async def test_feed_item_event(self):
        item = "item"
        event = FeedItemEvent(item)

        self.assertEqual(event.item, item)

        self.assertTrue("FeedItemEvent" in event.__repr__())

        with self.assertRaises(NotImplementedError):
            await event.respond("You cannot respond to a feed item.")

    async def test_run_skill(self):
        opsdroid = OpsDroid(
            config={
                "connectors": [{"name": "rss"}],
                "skills": [
                    {
                        "name": "test",
                        "no-cache": True,
                        "path": os.path.join(
                            MODULE_ROOT, "..", "tests/mockmodules/skills/rss_skill"
                        ),
                    }
                ],
            }
        )
        await opsdroid.load()

        opsdroid.run_skill = amock.CoroutineMock()
        connector = ConnectorRSS({"name": "rss"}, opsdroid=opsdroid)
        connector._update_feed = amock.CoroutineMock()
        item = "item"

        await connector.connect()
        await connector._run_skills(list(connector._feeds.keys())[0], [item])

        self.assertTrue(opsdroid.run_skill.called)
        event = opsdroid.run_skill.call_args[0][2]
        self.assertTrue(event.connector is connector)
        self.assertTrue(event.item is item)
        self.assertTrue("example.com" in event.target)

        await opsdroid.unload()

    async def test_update_feed(self):
        connector = ConnectorRSS({"name": "rss"}, opsdroid={})
        with amock.patch(
            "aiohttp.ClientSession.get", new=amock.CoroutineMock
        ) as patched_request:
            mock_response = amock.CoroutineMock()
            patched_request.return_value = mock_response
            patched_request.__aenter__ = amock.CoroutineMock()
            patched_request.__aexit__ = amock.CoroutineMock()

            mock_response.content_type = "atom"
            with open(
                os.path.join(MODULE_ROOT, "..", "tests/responses/rss_new_feed.atom"),
                "rb",
            ) as mock_feed:
                mock_reader = amock.CoroutineMock()
                mock_reader.return_value = mock_feed.read()
                mock_response.read = mock_reader
                feed = await connector._update_feed("example url")
                self.assertTrue(isinstance(feed, atoma.atom.AtomFeed))

            mock_response.content_type = "rss"
            with open(
                os.path.join(MODULE_ROOT, "..", "tests/responses/rss_new_feed.rss"),
                "rb",
            ) as mock_feed:
                mock_reader = amock.CoroutineMock()
                mock_reader.return_value = mock_feed.read()
                mock_response.read = mock_reader
                feed = await connector._update_feed("example url")
                self.assertTrue(isinstance(feed, atoma.rss.RSSChannel))

            mock_response.content_type = "xml"
            feed = await connector._update_feed("example url")
            self.assertTrue(feed is None)
