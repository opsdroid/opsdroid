"""A helper function for parsing and executing regex skills."""

import logging
import re
import copy

_LOGGER = logging.getLogger(__name__)


async def calculate_score(regex, score_factor):
    """Calculate the score of a regex."""
    # The score asymptotically approaches the max score
    # based on the length of the expression.
    return (1 - (1 / ((len(regex) + 1) ** 2))) * score_factor


async def parse_regex(opsdroid, skills, message):
    """Parse a message against all regex skills."""
    matched_skills = []
    for skill in skills:
        for matcher in skill.matchers:
            if "regex" in matcher:
                opts = matcher["regex"]
                if opts["case_sensitive"]:
                    regex = re.search(opts["expression"],
                                      message.text)
                else:
                    regex = re.search(opts["expression"],
                                      message.text, re.IGNORECASE)
                if regex:
                    new_message = copy.copy(message)
                    new_message.regex = regex
                    matched_skills.append({
                        "score": await calculate_score(
                            opts["expression"], opts["score_factor"]),
                        "skill": skill,
                        "config": skill.config,
                        "message": new_message
                    })
    return matched_skills
