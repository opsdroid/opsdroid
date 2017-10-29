"""A helper function for parsing and executing regex skills."""

import logging
import re


_LOGGER = logging.getLogger(__name__)


async def parse_regex(opsdroid, message):
    """Parse a message against all regex skills."""
    for skill in opsdroid.skills:
        if "regex" in skill:
            if skill["regex"]["case_sensitive"]:
                regex = re.search(skill["regex"]["expression"],
                                  message.text)
            else:
                regex = re.search(skill["regex"]["expression"],
                                  message.text, re.IGNORECASE)
            if regex:
                message.regex = regex
                await opsdroid.run_skill(skill["skill"],
                                         skill["config"], 
                                         message)
