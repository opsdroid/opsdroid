"""A helper function for parsing and executing Dialogflow skills."""

import logging
import json

import aiohttp


_LOGGER = logging.getLogger(__name__)


async def call_dialogflow(message, config, lang):
    """Call the Dialogflow api and return the response."""
    async with aiohttp.ClientSession() as session:
        payload = {
            "v": "20150910",
            "lang": lang,
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
        _LOGGER.info("Dialogflow response - %s", json.dumps(result))

        return result


async def parse_dialogflow(opsdroid, message, config):
    """Parse a message against all Dialogflow skills."""
    matched_skills = []
    if 'access-token' in config:
        try:
            result = await call_dialogflow(message, config,
                                           opsdroid.config.get("language", "en"))
        except aiohttp.ClientOSError:
            _LOGGER.error("No response from Dialogflow, check your network.")
            return matched_skills

        if result["status"]["code"] >= 300:
            _LOGGER.error("Dialogflow error - %s  - %s",
                          str(result["status"]["code"]),
                          result["status"]["errorType"])
            return matched_skills

        if "min-score" in config and \
                result["result"]["score"] < config["min-score"]:
            _LOGGER.debug("Dialogflow score lower than min-score")
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
                        _LOGGER.debug("Matched against skill %s",
                                      skill["config"]["name"])
                        matched_skills.append({
                            "score": result["result"]["score"],
                            "skill": skill["skill"],
                            "config": skill["config"],
                            "message": message
                        })
    return matched_skills
