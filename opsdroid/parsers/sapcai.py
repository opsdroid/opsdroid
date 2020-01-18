"""A helper function for parsing and executing Recast.AI skills."""
import logging
import json

import aiohttp
from voluptuous import Required

from opsdroid.const import DEFAULT_LANGUAGE
from opsdroid.const import SAPCAI_API_ENDPOINT


_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = {Required("token"): str, "min-score": float}


async def call_sapcai(message, config, lang=DEFAULT_LANGUAGE):
    """Call the SAP Conversational AI api and return the response."""
    async with aiohttp.ClientSession(trust_env=True) as session:
        payload = {"language": lang, "text": message.text}
        headers = {
            "Authorization": "Token " + config["token"],
            "Content-Type": "application/json",
        }
        resp = await session.post(
            SAPCAI_API_ENDPOINT, data=json.dumps(payload), headers=headers
        )
        result = await resp.json()
        _LOGGER.info(_("SAP Conversational AI response - %s."), json.dumps(result))

        return result


async def parse_sapcai(opsdroid, skills, message, config):
    """Parse a message against all SAP Conversational AI intents."""
    matched_skills = []
    language = config.get("lang") or opsdroid.config.get("lang", DEFAULT_LANGUAGE)

    if "token" in config:
        try:
            result = await call_sapcai(message, config, language)
        except aiohttp.ClientOSError:
            _LOGGER.error(
                _("No response from SAP Conversational.AI, check your network.")
            )
            return matched_skills

        if result["results"] is None:
            _LOGGER.error(_("SAP Conversational AI error - %s."), result["message"])
            return matched_skills

        if not result["results"]["intents"]:
            _LOGGER.error(
                _(
                    "SAP Conversational AI error - "
                    "No intent found "
                    "for the message %s"
                ),
                str(message.text),
            )
            return matched_skills

        confidence = result["results"]["intents"][0]["confidence"]

        if "min-score" in config and confidence < config["min-score"]:
            _LOGGER.debug(_("SAP Conversational AI score lower than min-score."))
            return matched_skills

        if result:
            for skill in skills:
                for matcher in skill.matchers:
                    if "sapcai_intent" in matcher:
                        if (
                            matcher["sapcai_intent"]
                            in result["results"]["intents"][0]["slug"]
                        ):
                            message.sapcai = result
                            for key, entity in (
                                result["results"].get("entities", {}).items()
                            ):
                                message.update_entity(
                                    key, entity[0]["raw"], entity[0]["confidence"]
                                )
                            _LOGGER.debug(
                                _("Matched against skill %s."), skill.config["name"]
                            )

                            matched_skills.append(
                                {
                                    "score": confidence,
                                    "skill": skill,
                                    "config": skill.config,
                                    "message": message,
                                }
                            )
    return matched_skills
