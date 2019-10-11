"""A helper function for parsing and executing IBM watson skills."""
import logging
import json

from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import ApiException

from opsdroid.const import WATSON_API_ENDPOINT
from opsdroid.const import WATSON_API_VERSION

_LOGGER = logging.getLogger(__name__)


async def get_session_id(service, config):
    """Authenticate and get session id from watson."""
    service.set_service_url(
        "https://{}{}".format(config["gateway"], WATSON_API_ENDPOINT)
    )
    response = service.create_session(assistant_id=config["assistant-id"]).get_result()

    config["session-id"] = response["session_id"]


async def call_watson(message, config):
    """Call the IBM Watson api and return the response."""
    authenticator = IAMAuthenticator(config["access-token"])
    service = AssistantV2(version=WATSON_API_VERSION, authenticator=authenticator)

    await get_session_id(service, config)

    response = service.message(
        assistant_id=config["assistant-id"],
        session_id=config["session-id"],
        input={"message_type": "text", "text": message.text},
    ).get_result()

    _LOGGER.info(_("Watson response - %s"), json.dumps(response))

    return response


async def parse_watson(opsdroid, skills, message, config):
    """Parse a message against all IBM Watson skills."""
    matched_skills = []
    try:
        result = await call_watson(message, config)
    except KeyError as error:
        _LOGGER.error(
            _("Error: %s . You are probably missing some configuration parameter."),
            error,
        )
    except ApiException as ex:
        _LOGGER.error(_("Watson Api error - %d:%s"), ex.code, ex.message)

    if not result["output"]["intents"]:
        _LOGGER.error(_("Watson - No intent found. Did you forget to create one?"))
        return matched_skills

    try:
        confidence = result["output"]["intents"][0]["confidence"]
    except KeyError:
        confidence = 0.0

    if "min-score" in config and confidence < config["min-score"]:
        _LOGGER.info(_("Watson score lower than min-score"))
        return matched_skills

    if result:
        for skill in skills:
            for matcher in skill.matchers:
                if "watson_intent" in matcher:
                    if matcher["watson_intent"] in [
                        i["value"] for i in result["output"]["intents"][0]["intent"]
                    ]:
                        message.watson = result
                        for key, entity in result["output"]["intents"][0].items():
                            if key != "intent":
                                await message.update_entity(key, entity["confidence"])
                        matched_skills.append(
                            {
                                "score": confidence,
                                "skill": skill,
                                "config": skill.config,
                                "message": message,
                            }
                        )
    return matched_skills
