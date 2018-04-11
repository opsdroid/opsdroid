"""A helper function for parsing and executing regex skills."""

import logging
from parse import parse

from opsdroid.parsers.regex import calculate_score


_LOGGER = logging.getLogger(__name__)


async def parse_format(opsdroid, message):
    """Parse a message against all parse_format skills."""
    matched_skills = []
    for skill in opsdroid.skills:
        if "parse_format" in skill:
            result = parse(skill["parse_format"], message.text)
            if result:
                message.parse_result = result
                matched_skills.append({
                    "score": await calculate_score(skill["parse_format"]),
                    "skill": skill["skill"],
                    "config": skill["config"],
                    "message": message
                })
    return matched_skills
