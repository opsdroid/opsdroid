"""A helper function for parsing and executing luis.ai skills."""

import logging
import json
import contextlib

import aiohttp

from opsdroid.const import LUISAI_DEFAULT_URL

_LOGGER = logging.getLogger(__name__)


async def call_luisai(message, config):
    """Call the luis.ai api and return the response."""
    async with aiohttp.ClientSession() as session:
        headers = {
            "Content-Type": "application/json"
        }
        url = LUISAI_DEFAULT_URL
        resp = await session.get(url + config['appid'] +
                                 '?subscription-key=' + config['appkey'] +
                                 '&timezoneOffset=0' +
                                 '&verbose=' + str(config['verbose']) +
                                 '&q=' + message.text, headers=headers)
        result = await resp.json()
        _LOGGER.debug(_("luis.ai response - %s"), json.dumps(result))

        return result


async def parse_luisai(opsdroid, message, config):
    """Parse a message against all luisai skills."""
    matched_skills = []
    if 'appid' in config and 'appkey' in config:
        try:
            result = await call_luisai(message, config)
        except aiohttp.ClientOSError:
            _LOGGER.error(_("No response from luis.ai, check your network."))
            return matched_skills

        if result:

            # if there is an error (eg. 404 error)
            # luis.ai responds with a status code
            with contextlib.suppress(KeyError):
                if result["statusCode"] >= 300:
                    _LOGGER.error(_("luis.ai error - %s %s"),
                                  str(result["statusCode"]),
                                  result["message"])

            if "min-score" in config and \
                    result["topScoringIntent"]["score"] \
                    < config["min-score"]:
                _LOGGER.debug(_("luis.ai score lower than min-score"))
                return matched_skills

            for skill in opsdroid.skills:
                if "luisai_intent" in skill:
                    try:
                        intents = [i["intent"] for i in result["intents"]]
                    except KeyError:
                        continue

                    if skill["luisai_intent"] in intents:
                        message.luisai = result
                        matched_skills.append({
                            "score": result["topScoringIntent"]["score"],
                            "skill": skill["skill"],
                            "config": skill["config"],
                            "message": message
                        })
    return matched_skills
