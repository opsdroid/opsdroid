"""A helper function for parsing and executing Dialogflow skills."""

import logging
import json

import aiohttp
import dialogflow

# import dialogflow_v2 as dialogflow

from opsdroid.const import (
    DEFAULT_LANGUAGE,
    DIALOGFLOW_API_VERSION,
    DIALOGFLOW_API_ENDPOINT,
)


_LOGGER = logging.getLogger(__name__)


async def parse_dialogflow(opsdroid, skills, message, config):
    """Parse a message against all Dialogflow skills."""
    session_client = dialogflow.SessionsClient()
    project_id = config.get("project-id")

    session = session_client.session_path(project_id, "opsdroid")
    text_input = dialogflow.types.TextInput(
        text=message.text, language_code=DEFAULT_LANGUAGE
    )
    query_input = dialogflow.types.QueryInput(text=text_input)

    response = session_client.detect_intent(session=session, query_input=query_input)

    _LOGGER.info("Query text: {}".format(response.query_result.query_text))
    _LOGGER.info(
        "Detected intent: {} (confidence: {})\n".format(
            response.query_result.intent.display_name,
            response.query_result.intent_detection_confidence,
        )
    )
    _LOGGER.info(
        "Fulfillment text: {}\n".format(response.query_result.fulfillment_text)
    )

    # matched_skills = []
    # if "access-token" in config:
    #     try:
    #         result = await call_dialogflow(
    #             message, config, opsdroid.config.get("lang", DEFAULT_LANGUAGE)
    #         )
    #     except aiohttp.ClientOSError:
    #         _LOGGER.error(_("No response from Dialogflow, " "check your network."))
    #         return matched_skills
    #
    #     if result["status"]["code"] >= 300:
    #         _LOGGER.error(
    #             _("Dialogflow error - %s  - %s"),
    #             str(result["status"]["code"]),
    #             result["status"]["errorType"],
    #         )
    #         return matched_skills
    #
    #     if "min-score" in config and result["result"]["score"] < config["min-score"]:
    #         _LOGGER.debug(_("Dialogflow score lower than min-score"))
    #         return matched_skills
    #
    #     if result:
    #
    #         for skill in skills:
    #             for matcher in skill.matchers:
    #
    #                 if "dialogflow_action" in matcher or "dialogflow_intent" in matcher:
    #                     if (
    #                         "action" in result["result"]
    #                         and matcher["dialogflow_action"]
    #                         in result["result"]["action"]
    #                     ) or (
    #                         "intentName" in result["result"]
    #                         and matcher["dialogflow_intent"]
    #                         in result["result"]["intentName"]
    #                     ):
    #                         message.dialogflow = result
    #                         message.apiai = message.dialogflow
    #                         _LOGGER.debug(
    #                             _("Matched against skill %s"), skill.config["name"]
    #                         )
    #                         matched_skills.append(
    #                             {
    #                                 "score": result["result"]["score"],
    #                                 "skill": skill,
    #                                 "config": skill.config,
    #                                 "message": message,
    #                             }
    #                         )
    # return matched_skills
