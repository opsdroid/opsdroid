"""A helper function for parsing and executing mention skills."""

import logging
import re


_LOGGER = logging.getLogger(__name__)


async def parse_mention(opsdroid, skills, message):
    """Parse a message if the bot is mentioned.

    Args:
        opsdroid (OpsDroid): An instance of opsdroid.core.
        skills (list): A list containing all skills available.
        message(object): An instance of events.message.

    Return:
        Either empty list or a list containing all matched skills.
    """

    matched_skills = []
    mentions = {}

    for connector in opsdroid.connectors:
        if connector.config["name"] == "matrix":
            mentions.update({"matrix": connector.config["mxid"]})

    for skill in skills:
        for matcher in skill.matchers:
            if "mention" in matcher:
                if "matrix" in mentions:
                    if "formatted_body" in message.raw_event["content"] and re.search(
                        "https://matrix.to/#/" + mentions["matrix"],
                        message.raw_event["content"]["formatted_body"],
                    ):
                        matched_skills.append(
                            {
                                "score": 1,
                                "skill": skill,
                                "config": skill.config,
                                "message": message,
                            }
                        )

    return matched_skills
