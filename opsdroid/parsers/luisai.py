"""A helper function for parsing and executing luis.ai skills."""

import logging
import json

import aiohttp


_LOGGER = logging.getLogger(__name__)


async def call_luisai(message, config):
    """Call the luis.ai api and return the response."""
    async with aiohttp.ClientSession() as session:
        headers = {
            "Content-Type": "application/json"
        }
        url = 'https://westus.api.cognitive.microsoft.com/luis/v2.0/apps/'
        resp = await session.get(url + config['appid'] +
                                 '?subscription-key=' + config['appkey'] +
                                 '&timezoneOffset=0' +
                                 '&verbose=' + str(config['verbose']) +
                                 '&q=' + message.text, headers=headers)
        result = await resp.json()
        _LOGGER.debug("luis.ai response - %s", json.dumps(result))

        return result


async def parse_luisai(opsdroid, message, config):
    """Parse a message against all luisai skills."""
    if 'appid' in config and 'appkey' in config:
        try:
            result = await call_luisai(message, config)
        except aiohttp.ClientOSError:
            _LOGGER.error("No response from luis.ai, check your network.")
            return

        if result:

            # if there is an error (eg. 404 error)
            # luis.ai responds with a status code
            try:
                if result["statusCode"] >= 300:
                    _LOGGER.error("luis.ai error - %s %s",
                                  str(result["statusCode"]), result["message"])
            except KeyError:
                pass

            if "min-score" in config and \
                    result["topScoringIntent"]["score"] \
                    < config["min-score"]:
                _LOGGER.debug("luis.ai score lower than min-score")
                return

            for skill in opsdroid.skills:
                if "luisai_intent" in skill:
                    try:
                        intents = [i["intent"] for i in result["intents"]]
                    except KeyError:
                        continue

                    if skill["luisai_intent"] in intents:
                        message.luisai = result
                        await opsdroid.run_skill(skill["skill"],
                                                 skill["config"], 
                                                 message)
