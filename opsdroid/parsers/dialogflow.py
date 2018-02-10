"""A helper function for parsing and executing Dialogflow skills."""

import logging
import json

import aiohttp

from opsdroid.const import DEFAULT_LANGUAGE,\
                           DIALOGFLOW_API_VERSION,\
                           DIALOGFLOW_API_ENDPOINT


_LOGGER = logging.getLogger(__name__)


async def call_dialogflow(message, config, lang=DEFAULT_LANGUAGE):
    """Call the Dialogflow api and return the response."""
    async with aiohttp.ClientSession() as session:
        payload = {
            "v": DIALOGFLOW_API_VERSION,
            "lang": lang,
            "sessionId": message.connector.name,
            "query": message.text
        }
        headers = {
            "Authorization": "Bearer " + config['access-token'],
            "Content-Type": "application/json"
        }
        resp = await session.post(DIALOGFLOW_API_ENDPOINT,
                                  data=json.dumps(payload),
                                  headers=headers)
        result = await resp.json()
        _LOGGER.info(_("Dialogflow response - %s"), json.dumps(result))

        return result


async def parse_dialogflow(opsdroid, message, config):
    """Parse a message against all Dialogflow skills."""
    matched_skills = []
    if 'access-token' in config:
        try:
            result = await call_dialogflow(message, config,
                                           opsdroid.config.get(
                                               "lang", DEFAULT_LANGUAGE))
        except aiohttp.ClientOSError:
            _LOGGER.error(_("No response from Dialogflow, "
                            "check your network."))
            return matched_skills

        if result["status"]["code"] >= 300:
            _LOGGER.error(_("Dialogflow error - %s  - %s"),
                          str(result["status"]["code"]),
                          result["status"]["errorType"])
            return matched_skills

        if "min-score" in config and \
                result["result"]["score"] < config["min-score"]:
            _LOGGER.debug(_("Dialogflow score lower than min-score"))
            return matched_skills

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
                        message.apiai = message.dialogflow
                        _LOGGER.debug(_("Matched against skill %s"),
                                      skill["config"]["name"])
                        matched_skills.append({
                            "score": result["result"]["score"],
                            "skill": skill["skill"],
                            "config": skill["config"],
                            "message": message
                        })
    return matched_skills
