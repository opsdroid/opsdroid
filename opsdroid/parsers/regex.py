"""A helper function for parsing and executing regex skills."""

import logging
import re

_LOGGER = logging.getLogger(__name__)


async def calculate_score(regex, score_factor):
    """Calculate the score of a regex."""
    # The score asymptotically approaches the max score
    # based on the length of the expression.
    return (1 - (1 / ((len(regex) + 1) ** 2))) * score_factor


async def match_regex(text, opts):
    """Return False if matching does not need to be case sensitive."""
    def is_case_sensitive():
        if opts["case_sensitive"]:
            return False
        return re.IGNORECASE

    if opts["matching_condition"].lower() == "search":
        regex = re.search(opts["expression"], text, is_case_sensitive())
    elif opts["matching_condition"].lower() == "fullmatch":
        regex = re.fullmatch(opts["expression"], text, is_case_sensitive())
    else:
        regex = re.match(opts["expression"], text, is_case_sensitive())
    return regex


async def parse_regex(opsdroid, skills, message):
    """Parse a message against all regex skills."""
    matched_skills = []
    for skill in skills:
        for matcher in skill.matchers:
            if "regex" in matcher:
                opts = matcher["regex"]
                regex = await match_regex(message.text, opts)
                if regex:
                    message.regex = regex
                    matched_skills.append({
                        "score": await calculate_score(
                            opts["expression"], opts["score_factor"]),
                        "skill": skill,
                        "config": skill.config,
                        "message": message
                    })
    return matched_skills
