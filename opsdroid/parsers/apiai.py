"""A helper function for parsing and executing api.ai skills."""

import logging
import json

import aiohttp


async def call_apiai(message, config):
    """Call the api.ai api and return the response."""
    async with aiohttp.ClientSession() as session:
        payload = {
            "v": "20150910",
            "lang": "en",
            "sessionId": message.connector.name,
            "query": message.text
        }
        headers = {
            "Authorization": "Bearer " + config['access-token'],
            "Content-Type": "application/json"
        }
        resp = await session.post("https://api.api.ai/v1/query",
                                  data=json.dumps(payload),
                                  headers=headers)
        result = await resp.json()
        logging.debug("api.ai response - " + json.dumps(result))

        return result


async def parse_apiai(opsdroid, message):
    """Parse a message against all apiai skills."""
    # pylint: disable=broad-except
    # We want to catch all exceptions coming from a skill module and not
    # halt the application. If a skill throws an exception it just doesn't
    # give a response to the user, so an error response should be given.
    config = opsdroid.config['parsers']['apiai']
    if 'access-token' in config:

        result = await call_apiai(message, config)

        if result["status"]["code"] >= 300:
            logging.error("api.ai error - " +
                          str(result["status"]["code"]) + " " +
                          result["status"]["errorType"])
            return

        if "min-score" in config and \
                result["result"]["score"] < config["min-score"]:
            logging.debug("api.ai score lower than min-score")
            return

        if result:
            for skill in opsdroid.skills:

                if "apiai_action" in skill or "apiai_intent" in skill:
                    if ("action" in result["result"] and
                            skill["apiai_action"] in
                            result["result"]["action"]) \
                            or ("intentName" in result["result"] and
                                skill["apiai_intent"] in
                                result["result"]["intentName"]):
                        message.apiai = result
                        try:
                            await skill["skill"](opsdroid, message)
                        except Exception:
                            await message.respond(
                                "Whoops there has been an error")
                            await message.respond(
                                "Check the log for details")
                            logging.exception("Exception when parsing '" +
                                              message.text +
                                              "' against skill '" +
                                              result["result"]["action"] + "'")
