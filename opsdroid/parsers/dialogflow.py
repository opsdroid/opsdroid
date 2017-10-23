"""A helper function for parsing and executing Dialogflow skills."""

import logging
import json

import aiohttp


_LOGGER = logging.getLogger(__name__)


async def call_dialogflow(message, config):
    """Call the Dialogflow api and return the response."""
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
        resp = await session.post("https://api.dialogflow.com/v1/query",
                                  data=json.dumps(payload),
                                  headers=headers)
        result = await resp.json()
        _LOGGER.debug("Dialogflow response - " + json.dumps(result))

        return result


async def parse_dialogflow(opsdroid, message, config):
    """Parse a message against all Dialogflow skills."""
    # pylint: disable=broad-except
    # We want to catch all exceptions coming from a skill module and not
    # halt the application. If a skill throws an exception it just doesn't
    # give a response to the user, so an error response should be given.
    if 'access-token' in config:
        try:
            result = await call_dialogflow(message, config)
        except aiohttp.ClientOSError:
            _LOGGER.error("No response from Dialogflow, check your network.")
            return

        if result["status"]["code"] >= 300:
            _LOGGER.error("Dialogflow error - " +
                          str(result["status"]["code"]) + " " +
                          result["status"]["errorType"])
            return

        if "min-score" in config and \
                result["result"]["score"] < config["min-score"]:
            _LOGGER.debug("Dialogflow score lower than min-score")
            return

        if result:
            for skill in opsdroid.skills:

                if "dialogflow_action" in skill or \
                                "dialogflow_intent" in skill:
                    if ("action" in result["result"] and
                            skill["dialogflow_action"] in
                            result["result"]["action"]) \
                            or ("intentName" in result["result"] and
                                skill["dialogflow_intent"] in
                                result["result"]["intentName"]):
                        message.dialogflow = result
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
                                              result["result"]["action"] + "'")
