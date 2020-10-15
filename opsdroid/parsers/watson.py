"""A helper function for parsing and executing IBM watson skills."""
import logging
import contextlib
from voluptuous import Required

from opsdroid.const import WATSON_API_ENDPOINT, WATSON_API_VERSION


# This exception needs to be set outside the call_watson to be called
with contextlib.suppress(ImportError):
    from ibm_watson import ApiException  # noqa F401

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = {
    Required("gateway"): str,
    Required("assistant-id"): str,
    Required("token"): str,
    "min-score": float,
}


async def get_all_entities(entities):
    """Get all entities on the same dict.

    Watson API will return a list containing dictionaries for each,
    entity found. On large numbers of entities it becomes hard to get
    what we want, this function is meant to be an helper function to get
    all the entities into a concise dictionary containing {<string>:<list>}

    Return:
        Dictionary containing entities name and list of values.

    """
    entities_dict = dict()
    for entity in entities:
        name = entity["entity"]
        val = entity["value"]

        entities_dict.setdefault(name, []).append(val)
    return entities_dict


async def get_session_id(service, config):
    """Authenticate and get session id from watson.

    Watson API expects you to get the session id first before using
    the API. So far it seems that each request made through the API has
    to have its own session id.

    This helper function makes it easier to get the id and inject it into
    the configuration.

    """
    service.set_service_url(WATSON_API_ENDPOINT.format(gateway=config["gateway"]))
    response = service.create_session(assistant_id=config["assistant-id"]).get_result()

    config["session-id"] = response["session_id"]


async def call_watson(message, opsdroid, config):
    """Call the IBM Watson api and return the response.

    Main function used to call Watson API by using the official
    watson dependency for python.  We use get_result() to get the
    response on a dict format - without this the response is of type
    'ibm_cloud_sdk_core.detailed_response.DetailedResponse' and will
    show everything from the request including headers.

    Return:
        A dict containing the API response

    """
    try:
        from ibm_watson import AssistantV2
        from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

        authenticator = IAMAuthenticator(config["token"])
        service = AssistantV2(version=WATSON_API_VERSION, authenticator=authenticator)

        await get_session_id(service, config)

        response = service.message(
            assistant_id=config["assistant-id"],
            session_id=config["session-id"],
            input={"message_type": "text", "text": message.text},
        ).get_result()

        _LOGGER.debug(_("Watson response - %s."), response)

        return response

    except ImportError:
        _LOGGER.error(
            _(
                "Unable to find ibm_watson dependency. Please install ibm_watson with the command pip install ibm_watson if you want to use this parser."
            )
        )
        opsdroid.config["parsers"][0]["enabled"] = False


async def parse_watson(opsdroid, skills, message, config):
    """Parse a message against all IBM Watson skills.

    Since the official watson dependency throws their own exceptions,
    we are using a try/excerpt and check if ApiException is thrown.
    This exception contains a code, a message and info (contains
    additional info about the error, but we are not using it at the
    moment).

    Since we need a few things to be present on the configuration file,
    we also check if all the needed keys are in the configuration otherwise
    we will log an error.

    Args:
        opsdroid (OpsDroid): An instance of opsdroid.core.
        skills (list): A list containing all skills available.
        message(object): An instance of events.message.
        config (dict): configuration settings from the
            file config.yaml.

    Return:
        Either empty list or a list containing all matched skills.

    """
    matched_skills = []
    try:
        result = await call_watson(message, opsdroid, config)

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
                        if (
                            matcher["watson_intent"]
                            in result["output"]["intents"][0]["intent"]
                        ):
                            message.raw_parses["watson"] = result

                            entities = await get_all_entities(
                                result["output"]["entities"]
                            )
                            for key, value in entities.items():
                                message.update_entity(
                                    key,
                                    value,
                                    result["output"]["intents"][0]["confidence"],
                                )

                            matched_skills.append(
                                {
                                    "score": confidence,
                                    "skill": skill,
                                    "config": skill.config,
                                    "message": message,
                                }
                            )

    except KeyError as error:
        _LOGGER.error(
            _("Error: %s"),
            error,
        )
    except ApiException as ex:
        _LOGGER.error(_("Watson Api error - %d:%s."), ex.code, ex.message)

    return matched_skills
