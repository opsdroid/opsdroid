"""A helper function for parsing and executing regex skills."""

import logging
import re

from opsdroid.const import REGEX_MAX_SCORE


_LOGGER = logging.getLogger(__name__)


async def calculate_score(regex):
    """Calculate the score of a regex."""
    # The score asymptotically approaches the max score
    # based on the length of the expression.
    return (1 - (1 / ((len(regex) + 1) ** 2))) * REGEX_MAX_SCORE


async def parse_regex(opsdroid, message):
    """Parse a message against all regex skills."""
    matched_skills = []
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
                matched_skills.append({
                    "score": await calculate_score(
                        skill["regex"]["expression"]),
                    "skill": skill["skill"],
                    "config": skill["config"],
                    "message": message
                })
    return matched_skills
