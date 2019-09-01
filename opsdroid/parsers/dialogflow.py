"""A helper function for parsing and executing Dialogflow skills."""
import os
import logging

import dialogflow

from opsdroid.const import DEFAULT_LANGUAGE


_LOGGER = logging.getLogger(__name__)


async def call_dialogflow(text, config):
    """Call the Dialogflow api and return the response."""

    if os.environ["GOOGLE_APPLICATION_CREDENTIALS"]:
        session_client = dialogflow.SessionsClient()
        project_id = config.get("project-id")

        session = session_client.session_path(project_id, "opsdroid")
        text_input = dialogflow.types.TextInput(
            text=text, language_code=DEFAULT_LANGUAGE
        )
        query_input = dialogflow.types.QueryInput(text=text_input)

        response = session_client.detect_intent(
            session=session, query_input=query_input
        )

        return response
    else:
        raise Warning(
            "Authentication file not found, dialogflow parser will not be available"
        )


async def parse_dialogflow(opsdroid, skills, message, config):
    """Parse a message against all Dialogflow skills."""
    try:
        result = await call_dialogflow(message.text, config)
        matched_skills = []
        if (
            "min-score" in config
            and result.query_result.intent_detection_confidence < config["min-score"]
        ):
            _LOGGER.debug(_("Dialogflow score lower than min-score"))
            return matched_skills

        if result:

            for skill in skills:
                for matcher in skill.matchers:

                    if "dialogflow_action" in matcher or "dialogflow_intent" in matcher:
                        if (
                            "action" in result.query_result
                            and matcher["dialogflow_action"]
                            in result.query_result.action
                        ) or (
                            "intentName" in result.query_result
                            and matcher["dialogflow_intent"]
                            in result.query_result.intent.display_name
                        ):
                            message.dialogflow = result.query_result

                            _LOGGER.debug(
                                _("Matched against skill %s"), skill.config["name"]
                            )
                            matched_skills.append(
                                {
                                    "score": result.query_result.intent_detection_confidence,
                                    "skill": skill,
                                    "config": skill.config,
                                    "message": message,
                                }
                            )
        return matched_skills

    except Exception as error:
        _LOGGER.error(
            "Oops, there was an error while connecting to dialogflow - {}".format(error)
        )
