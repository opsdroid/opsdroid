"""A helper function for parsing and executing mention skills."""

import logging


_LOGGER = logging.getLogger(__name__)


async def parse_mention(opsdroid, skills, message):
    """Parse a message if the bot is mentioned."""
    matched_skills = []
    mentions = {}

    for connector in opsdroid.connectors:
        if connector.config["name"] == "matrix":
            mentions.update({"matrix": connector.config["mxid"]})

    for skill in skills:
        for matcher in skill.matchers:
            if "mention" in matcher:
                if "matrix" in mentions:
                    if "formatted_body" in message.raw_event["content"] and (
                        '<a href="https://matrix.to/#/' + mentions["matrix"] + '">'
                        in message.raw_event["content"]["formatted_body"]
                        or "<a href='https://matrix.to/#/" + mentions["matrix"] + "'>"
                        in message.raw_event["content"]["formatted_body"]
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
