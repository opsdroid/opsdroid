"""A helper function for parsing and executing always skills."""

import logging


_LOGGER = logging.getLogger(__name__)


async def parse_always(opsdroid, message):
    """Parse a message always."""
    for skill in opsdroid.skills:
        for matcher in skill.matchers:
            if "always" in matcher:
                await opsdroid.run_skill(skill, skill.config, message)
