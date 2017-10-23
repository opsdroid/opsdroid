"""A helper function for parsing and executing wit.ai skills."""

import logging
import json

import aiohttp

_LOGGER = logging.getLogger(__name__)


async def call_witai(message, config):
    """Call the wit.ai api and return the response."""
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": "Bearer " + config['access-token']
        }
        payload = {
            "v": "20170307",
            "q": message.text
        }
        resp = await session.get("https://api.wit.ai/message?v={}&q={}".format(
            payload['v'], payload['q']), headers=headers)
        result = await resp.json()
        _LOGGER.debug("wit.ai response - " + json.dumps(result))
        _LOGGER.info(result)
        return result


async def parse_witai(opsdroid, message, config):
    """Parse a message against all witai skills."""
    # pylint: disable=broad-except
    # We want to catch all exceptions coming from a skill module and not
    # halt the application. If a skill throws an exception it just doesn't
    # give a response to the user, so an error response should be given.
    if 'access-token' in config:
        try:
            result = await call_witai(message, config)
        except aiohttp.ClientOSError:
            _LOGGER.error("No response from wit.ai, check your network.")
            return

        if 'code' in result:
            _LOGGER.error("wit.ai error - " + str(result['code'])
                          + " " + str(result['error']))
            return
        elif result['entities'] == {}:
            _LOGGER.error("wit.ai error - No intent found. Did you "
                          "forget to create one?")
            return

        try:
            confidence = result['entities']['intent'][0]['confidence']
        except KeyError:
            confidence = 0.0
        if "min-score" in config and confidence < config['min-score']:
            _LOGGER.debug("wit.ai score lower than min-score")
            return

        if result:
            for skill in opsdroid.skills:
                if "witai_intent" in skill:
                    if (skill['witai_intent'] in
                            [i['value'] for i in
                             result['entities']['intent']]):
                        message.witai = result
                        try:
                            await skill['skill'](opsdroid, skill['config'],
                                                 message)
                        except Exception:
                            parsed_skill = \
                                result['entities']['intent'][0]['value']
                            await message.respond(
                                "Whoops there has been an error")
                            await message.respond(
                                "Check the log for details")
                            _LOGGER.exception("Exception when parsing '" +
                                              message.text +
                                              "' against skill '" +
                                              parsed_skill + "'")
