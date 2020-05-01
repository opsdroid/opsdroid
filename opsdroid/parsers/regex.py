"""A helper function for parsing and executing regex skills."""

import logging
import regex

_LOGGER = logging.getLogger(__name__)


async def calculate_score(expression, score_factor):
    """Calculate the score of a regex."""
    # The score asymptotically approaches the max score
    # based on the length of the expression.
    return (1 - (1 / ((len(expression) + 1) ** 2))) * score_factor


async def match_regex(text, opts):
    """Return False if matching does not need to be case sensitive."""

    def is_case_sensitive():
        if opts["case_sensitive"]:
            return False
        return regex.IGNORECASE

    if opts["matching_condition"].lower() == "search":
        matched_regex = regex.search(opts["expression"], text, is_case_sensitive())
    elif opts["matching_condition"].lower() == "fullmatch":
        matched_regex = regex.fullmatch(opts["expression"], text, is_case_sensitive())
    else:
        matched_regex = regex.match(opts["expression"], text, is_case_sensitive())
    return matched_regex


async def parse_regex(opsdroid, skills, message):
    """Parse a message against all regex skills."""
    matched_skills = []
    for skill in skills:
        for matcher in skill.matchers:
            if "regex" in matcher:
                opts = matcher["regex"]
                matched_regex = await match_regex(message.text, opts)
                if matched_regex:
                    message.regex = matched_regex
                    for regroup, value in matched_regex.groupdict().items():
                        message.update_entity(regroup, value, None)
                    matched_skills.append(
                        {
                            "score": await calculate_score(
                                opts["expression"], opts["score_factor"]
                            ),
                            "skill": skill,
                            "config": skill.config,
                            "message": message,
                        }
                    )
    return matched_skills
