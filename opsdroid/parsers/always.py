"""A helper function for parsing and executing always skills."""

import logging


_LOGGER = logging.getLogger(__name__)


async def parse_always(opsdroid, message):
    """Parse a message always."""
    for skill in opsdroid.skills:
        if "always" in skill and skill["always"]:
            await opsdroid.run_skill(skill["skill"],
                                     skill["config"],
                                     message)
