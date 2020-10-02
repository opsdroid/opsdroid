"""A helper function for parsing and executing catch-all skills."""

import logging

_LOGGER = logging.getLogger(__name__)


async def parse_catchall(opsdroid, message):
    """Parse a message against catch-all skill, if found."""
    for skill in opsdroid.skills:
        for matcher in skill.matchers:
            if "catchall" in matcher:
                await opsdroid.run_skill(skill, skill.config, message)
