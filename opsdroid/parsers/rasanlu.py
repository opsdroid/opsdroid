"""A helper function for training, parsing and executing Rasa NLU skills."""

import logging
import json
import unicodedata

from hashlib import sha256

import aiohttp
import arrow

from opsdroid.const import RASANLU_DEFAULT_URL, RASANLU_DEFAULT_PROJECT

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = {"url": str, "project": str, "token": str, "min-score": float}


async def _get_all_intents(skills):
    """Get all skill intents and concatenate into a single markdown string."""
    intents = [skill["intents"] for skill in skills if skill["intents"] is not None]
    if not intents:
        return None
    intents = "\n\n".join(intents)
    return unicodedata.normalize("NFKD", intents).encode("ascii")


async def _get_intents_fingerprint(intents):
    """Return a hash of the intents."""
    return sha256(intents).hexdigest()


async def _build_training_url(config):
    """Build the url for training a Rasa NLU model."""
    url = "{}/train?project={}&fixed_model_name={}".format(
        config.get("url", RASANLU_DEFAULT_URL),
        config.get("project", RASANLU_DEFAULT_PROJECT),
        config["model"],
    )

    if "token" in config:
        url += "&token={}".format(config["token"])

    return url


async def _build_status_url(config):
    """Build the url for getting the status of Rasa NLU."""
    return "{}/status".format(config.get("url", RASANLU_DEFAULT_URL))


async def _init_model(config):
    """Make a request to force Rasa NLU to load the model into memory."""
    _LOGGER.info(_("Initialising Rasa NLU model."))

    initialisation_start = arrow.now()
    result = await call_rasanlu("", config)

    if result is None:
        _LOGGER.error(_("Initialisation failed, training failed.."))
        return False

    time_taken = int((arrow.now() - initialisation_start).total_seconds())
    _LOGGER.info(_("Initialisation complete in %s seconds."), time_taken)

    return True


async def _get_existing_models(config):
    """Get a list of models already trained in the Rasa NLU project."""
    project = config.get("project", RASANLU_DEFAULT_PROJECT)
    async with aiohttp.ClientSession(trust_env=True) as session:
        try:
            resp = await session.get(await _build_status_url(config))
            if resp.status == 200:
                result = await resp.json()
                if project in result["available_projects"]:
                    project_models = result["available_projects"][project]
                    return project_models["available_models"]
        except aiohttp.ClientOSError:
            pass
    return []


async def train_rasanlu(config, skills):
    """Train a Rasa NLU model based on the loaded skills."""
    _LOGGER.info(_("Starting Rasa NLU training."))
    intents = await _get_all_intents(skills)
    if intents is None:
        _LOGGER.warning(_("No intents found, skipping training."))
        return False

    config["model"] = await _get_intents_fingerprint(intents)
    if config["model"] in await _get_existing_models(config):
        _LOGGER.info(_("This model already exists, skipping training..."))
        await _init_model(config)
        return True

    async with aiohttp.ClientSession(trust_env=True) as session:
        _LOGGER.info(_("Now training the model. This may take a while..."))

        url = await _build_training_url(config)

        # https://github.com/RasaHQ/rasa_nlu/blob/master/docs/http.rst#post-train
        # Note : The request should always be sent as
        # application/x-yml regardless of wether you use
        # json or md for the data format. Do not send json as
        # application/json for example.+
        headers = {"content-type": "application/x-yml"}

        try:
            training_start = arrow.now()
            resp = await session.post(url, data=intents, headers=headers)
        except aiohttp.client_exceptions.ClientConnectorError:
            _LOGGER.error(_("Unable to connect to Rasa NLU, training failed."))
            return False

        if resp.status == 200:
            if resp.content_type == "application/json":
                result = await resp.json()
                if "info" in result and "new model trained" in result["info"]:
                    time_taken = (arrow.now() - training_start).total_seconds()
                    _LOGGER.info(
                        _("Rasa NLU training completed in %s seconds."), int(time_taken)
                    )
                    await _init_model(config)
                    return True

                _LOGGER.debug(result)
            if (
                resp.content_type == "application/zip"
                and resp.content_disposition.type == "attachment"
            ):
                time_taken = (arrow.now() - training_start).total_seconds()
                _LOGGER.info(
                    _("Rasa NLU training completed in %s seconds."), int(time_taken)
                )
                await _init_model(config)
                """
                As inditated in the issue #886, returned zip file is ignored, this can be changed
                This can be changed in future release if needed
                Saving model.zip file example :
                try:
                    output_file = open("/target/directory/model.zip","wb")
                    data = await resp.read()
                    output_file.write(data)
                    output_file.close()
                    _LOGGER.debug("Rasa taining model file saved to /target/directory/model.zip")
                except:
                    _LOGGER.error("Cannot save rasa taining model file to /target/directory/model.zip")
                """
                return True

        _LOGGER.error(_("Bad Rasa NLU response - %s."), await resp.text())
        _LOGGER.error(_("Rasa NLU training failed."))
        return False


async def call_rasanlu(text, config):
    """Call the Rasa NLU api and return the response."""
    async with aiohttp.ClientSession(trust_env=True) as session:
        headers = {}
        data = {
            "q": text,
            "project": config.get("project", "default"),
            "model": config.get("model", "fallback"),
        }
        if "token" in config:
            data["token"] = config["token"]
        url = config.get("url", RASANLU_DEFAULT_URL) + "/parse"
        try:
            resp = await session.post(url, data=json.dumps(data), headers=headers)
        except aiohttp.client_exceptions.ClientConnectorError:
            _LOGGER.error(_("Unable to connect to Rasa NLU."))
            return None
        if resp.status == 200:
            result = await resp.json()
            _LOGGER.debug(_("Rasa NLU response - %s."), json.dumps(result))
        else:
            result = await resp.text()
            _LOGGER.error(_("Bad Rasa NLU response - %s."), result)

        return result


async def parse_rasanlu(opsdroid, skills, message, config):
    """Parse a message against all Rasa NLU skills."""
    matched_skills = []
    try:
        result = await call_rasanlu(message.text, config)
    except aiohttp.ClientOSError:
        _LOGGER.error(_("No response from Rasa NLU, check your network."))
        return matched_skills

    if result == "unauthorized":
        _LOGGER.error(_("Rasa NLU error - Unauthorised request. Check your 'token'."))
        return matched_skills

    if result is None or "intent" not in result or result["intent"] is None:
        _LOGGER.error(
            _("Rasa NLU error - No intent found. Did you forget to create one?")
        )
        return matched_skills

    confidence = result["intent"]["confidence"]
    if "min-score" in config and confidence < config["min-score"]:
        _LOGGER.info(_("Rasa NLU score lower than min-score"))
        return matched_skills

    if result:
        for skill in skills:
            for matcher in skill.matchers:
                if "rasanlu_intent" in matcher:
                    if matcher["rasanlu_intent"] == result["intent"]["name"]:
                        message.rasanlu = result
                        for entity in result["entities"]:
                            message.update_entity(
                                entity["entity"], entity["value"], entity["confidence"]
                            )
                        matched_skills.append(
                            {
                                "score": confidence,
                                "skill": skill,
                                "config": skill.config,
                                "message": message,
                            }
                        )

    return matched_skills
