"""A helper function for parsing and executing Dialogflow skills."""
import os
import logging

from voluptuous import Required
from opsdroid.const import DEFAULT_LANGUAGE


_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = {Required("project-id"): str, "min-score": float}


async def call_dialogflow(text, opsdroid, config):
    """Call Dialogflow to get intent from text.

    Dialogflow will return an object with a few restrictions, you can't
    iterate it and the only way to access each element is by using dot
    notation.

    Args:
        text (string): message.text this is the text obtained from the user.
        opsdroid (OpsDroid): An instance of opsdroid.core.
        config (dict): configuration settings from the file config.yaml.

    Return:
        A 'google.cloud.dialogflow_v2.types.DetectIntentResponse' object.

    Raises:
        Warning: if Google credentials are not found in environmental
        variables or 'project-id' is not in config.

    """
    try:
        import dialogflow

        if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") and config.get(
            "project-id"
        ):
            session_client = dialogflow.SessionsClient()
            project_id = config.get("project-id")
            language = config.get("lang") or opsdroid.config.get(
                "lang", DEFAULT_LANGUAGE
            )

            session = session_client.session_path(project_id, "opsdroid")
            text_input = dialogflow.types.TextInput(text=text, language_code=language)
            query_input = dialogflow.types.QueryInput(text=text_input)

            response = session_client.detect_intent(
                session=session, query_input=query_input
            )

            return response
        else:
            raise Warning(
                _(
                    "Authentication file not found or 'project-id' not in configuration, dialogflow parser will not be available."
                )
            )
    except ImportError:
        _LOGGER.error(
            _(
                "Unable to find dialogflow dependency. Please install dialogflow with the command pip install dialogflow if you want to use this parser."
            )
        )
        opsdroid.config["parsers"][0]["enabled"] = False


async def parse_dialogflow(opsdroid, skills, message, config):
    """Parse a message against all Dialogflow skills.

    This function does a few things, first it will check if the
    intent confidence is higher than the minimum score set on config,
    then it will try to match an action or an intent to a matcher and
    add the proper skills to the skills list.

    At the moment a broad exception is being used due to the fact that
    dialogflow library doesn't have the best documentation yet and it's
    not possible to know what sort of exceptions the library will return.

    Args:
        opsdroid (OpsDroid): An instance of opsdroid.core.
        skills (list): A list containing all skills available.
        message(object): An instance of events.message.
        config (dict): configuration settings from the
            file config.yaml.

    Return:
        Either empty list or a list containing all matched skills.

    """
    try:
        result = await call_dialogflow(message.text, opsdroid, config)
        matched_skills = []
        if (
            "min-score" in config
            and result.query_result.intent_detection_confidence < config["min-score"]
        ):
            _LOGGER.debug(_("Dialogflow confidence lower than min-score."))
            return matched_skills

        if result:
            for skill in skills:
                for matcher in skill.matchers:
                    if "dialogflow_action" in matcher or "dialogflow_intent" in matcher:
                        if (
                            matcher.get("dialogflow_action")
                            == result.query_result.action
                        ) or (
                            matcher.get("dialogflow_intent")
                            == result.query_result.intent.display_name
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
        # TODO: Refactor broad exception
        _LOGGER.error(_("There was an error while parsing to dialogflow - %s."), error)
