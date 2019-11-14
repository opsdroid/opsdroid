# RSS Feed Matcher

## Configuring opsdroid

No configuration is needed for the RSS matcher.

## Matching RSS feed items

The RSS matcher allows you to specify the URL of an RSS or Atom feed and trigger a skill every time a new item is added to that feed.

## Example

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_rss
from opsdroid.events import Message

class RSSSkill(Skill):
    """An example RSS skill class."""

    @match_rss('https://examples.com/feed.rss', interval=30)
    async def myrssskill(self, event):
        """Send a message to our default room/connector when we get a new feed item."""
        await self.opsdroid.send(
            Message(f"Just got a new feed item called '{event.item.title}'.")
        )
```

The above skill would be called every time a new item is added to `https://examples.com/feed.rss` and the feed is checked every `30` seconds (the minimum is `5` seconds). Here we are constructing a new message that we are asking opsdroid to send in response to the feed item being created. By default because we haven't specified where this message should go opsdroid will send it to the default room on the default chat connector in your configuration.

The event you receive will be a `opsdroid.connector.rss.events.FeedItemEvent` which cannot be responded to and has an `item` attribute which will be either an `atoma.rss.RSSItem` or an `atoma.atom.AtomEntry` object depending on whether you are listening to an RSS or Atom feed. Check out [atoma](https://github.com/NicolasLM/atoma) for more information on these objects and their attributes.
