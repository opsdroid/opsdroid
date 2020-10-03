"""A helper function for parsing and executing catch-all skills."""

import logging

from opsdroid import events

_LOGGER = logging.getLogger(__name__)


async def parse_catchall(opsdroid, event):
    """Parse an event against catch-all skills, if found."""
    for skill in opsdroid.skills:
        for matcher in skill.matchers:
            if "catchall" in matcher:
                if (
                    matcher["messages_only"]
                    and isinstance(event, events.Message)
                    or not matcher["messages_only"]
                ):
                    await opsdroid.run_skill(skill, skill.config, event)
