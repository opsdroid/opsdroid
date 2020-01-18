"""A helper function for parsing and executing parse_format skills."""

import logging

from parse import parse, search

from opsdroid.parsers.regex import calculate_score


_LOGGER = logging.getLogger(__name__)


async def match_format(text, opts):
    """Match a message considering the options."""
    case_sensitive = opts["case_sensitive"]

    match_fn = parse
    if opts["matching_condition"].lower() == "search":
        match_fn = search

    return match_fn(opts["expression"], text, case_sensitive=case_sensitive)


async def parse_format(opsdroid, skills, message):
    """Parse a message against all parse_format skills."""
    matched_skills = []
    for skill in skills:
        for matcher in skill.matchers:
            if "parse_format" in matcher:
                opts = matcher["parse_format"]
                result = await match_format(message.text, opts)
                if result:
                    message.parse_result = result
                    _LOGGER.debug(result.__dict__)
                    for group, value in result.named.items():
                        message.update_entity(group, value, None)
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
