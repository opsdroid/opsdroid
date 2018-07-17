"""A helper function for parsing and executing Recast.AI skills."""
import logging
import json

import aiohttp

from opsdroid.const import DEFAULT_LANGUAGE
from opsdroid.const import RECASTAI_API_ENDPOINT


_LOGGER = logging.getLogger(__name__)


async def call_recastai(message, config, lang=DEFAULT_LANGUAGE):
    """Call the recastai api and return the response."""
    async with aiohttp.ClientSession() as session:
        payload = {
            "language": lang,
            "text": message.text
        }
        headers = {
            "Authorization": "Token " + config['access-token'],
            "Content-Type": "application/json"
        }
        resp = await session.post(RECASTAI_API_ENDPOINT,
                                  data=json.dumps(payload),
                                  headers=headers)
        result = await resp.json()
        _LOGGER.info(_("Recastai response - %s"), json.dumps(result))

        return result


async def parse_recastai(opsdroid, message, config):
    """Parse a message against all recastai intents."""
    matched_skills = []
    if 'access-token' in config:
        try:
            result = await call_recastai(message, config,
                                         opsdroid.config.get('lang',
                                                             DEFAULT_LANGUAGE))
        except aiohttp.ClientOSError:
            _LOGGER.error(_("No response from Recast.AI, check your network."))
            return matched_skills

        if result['results'] is None:
            _LOGGER.error(_("Recast.AI error - %s"), result["message"])
            return matched_skills

        if not result["results"]["intents"]:
            _LOGGER.error(_("Recast.AI error - No intent found "
                            "for the message %s"), str(message.text))
            return matched_skills

        if "min-score" in config and \
                result["results"]["intents"][0]["confidence"] < \
                config["min-score"]:
            _LOGGER.debug(_("Recast.AI score lower than min-score"))
            return matched_skills

        if result:
            for skill in opsdroid.skills:
                if "recastai_intent" in skill:
                    if (skill["recastai_intent"] in
                            result["results"]["intents"][0]["slug"]):
                        message.recastai = result
                        _LOGGER.debug(_("Matched against skill %s"),
                                      skill["config"]["name"])

                        matched_skills.append({
                            "score":
                                result["results"]["intents"][0]["confidence"],
                            "skill": skill["skill"],
                            "config": skill["config"],
                            "message": message
                        })
    return matched_skills
