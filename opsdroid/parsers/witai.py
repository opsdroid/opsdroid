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
        _LOGGER.info("wit.ai response - %s", json.dumps(result))
        return result


async def parse_witai(opsdroid, message, config):
    """Parse a message against all witai skills."""
    if 'access-token' in config:
        try:
            result = await call_witai(message, config)
        except aiohttp.ClientOSError:
            _LOGGER.error("No response from wit.ai, check your network.")
            return

        if 'code' in result:
            _LOGGER.error("wit.ai error - %s %s", str(result['code']),
                          str(result['error']))
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
            _LOGGER.info("wit.ai score lower than min-score")
            return

        if result:
            for skill in opsdroid.skills:
                if "witai_intent" in skill:
                    if (skill['witai_intent'] in
                            [i['value'] for i in
                             result['entities']['intent']]):
                        message.witai = result
                        await opsdroid.run_skill(skill["skill"],
                                                 skill["config"], 
                                                 message)
