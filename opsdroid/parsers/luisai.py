"""A helper function for parsing and executing luis.ai skills."""

import logging
import json

import aiohttp


_LOGGER = logging.getLogger(__name__)

async def call_luisai(message, config):
    """Call the luis.ai api and return the response."""
    async with aiohttp.ClientSession() as session:
        payload = {
            "subscription-key": config['appkey'],
            "q": message.text,
            "timezoneOffset": 0,
            "verbose": config['verbose']
        }
        headers = {
            "Content-Type": "application/json"
        }
        resp = await session.get('https://westus.api.cognitive.microsoft.com/luis/v2.0/apps/{}?subscription-key={}&timezoneOffset={}&verbose={}&q={}'
                                .format(config['appid'],config['appkey'],0,config['verbose'],message.text),
                                headers=headers)
        result = await resp.json()
        _LOGGER.debug("luis.ai response - " + json.dumps(result))

        return result

async def parse_luisai(opsdroid, message, config):
    """Parse a message against all luisai skills."""
    # pylint: disable=broad-except
    # We want to catch all exceptions coming from a skill module and not
    # halt the application. If a skill throws an exception it just doesn't
    # give a response to the user, so an error response should be given.
    if 'appid' in config and 'appkey' in config:
        try:
            result = await call_luisai(message, config)
        except aiohttp.ClientOSError:
            _LOGGER.error("No response from luis.ai, check your network.")
            return

        if result:

            # if there is an error (eg. 404 error), luis.ai responds with a status code
            try:
                if result["statusCode"] >= 300:
                    _LOGGER.error("luis.ai error - " +
                                  str(result["statusCode"]) + " " +
                                  result["message"])
                    return
            except:
                pass

            if "min-score" in config and \
                    result["topScoringIntent"]["score"] < config["min-score"]:
                _LOGGER.debug("luis.ai score lower than min-score")
                return

            for skill in opsdroid.skills:

                if "luisai_intent" in skill:
                    if (skill["luisai_intent"] in [i["intent"] for i in result["intents"]]):
                        message.luisai = result
                        try:
                            await skill["skill"](opsdroid, skill["config"],
                                                 message)
                        except Exception:
                            await message.respond(
                                "Whoops there has been an error")
                            await message.respond(
                                "Check the log for details")
                            _LOGGER.exception("Exception when parsing '" +
                                              message.text +
                                              "' against skill '" +
                                              result["query"] + "'")
