"""A helper function for training, parsing and executing Rasa NLU skills."""

import logging
import json
import unicodedata

from hashlib import sha256

import aiohttp
import arrow

from opsdroid.const import (
    RASANLU_DEFAULT_URL,
    RASANLU_DEFAULT_MODELS_PATH,
    RASANLU_DEFAULT_TRAIN_MODEL,
)

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = {
    "url": str,
    "token": str,
    "models-path": str,
    "min-score": float,
    "train": bool,
}


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
    url = "{}/model/train".format(
        config.get("url", RASANLU_DEFAULT_URL),
    )

    if "token" in config:
        url += "?&token={}".format(config["token"])

    return url


async def _build_status_url(config):
    """Build the url for getting the status of Rasa NLU."""
    url = "{}/status".format(config.get("url", RASANLU_DEFAULT_URL))
    if "token" in config:
        url += "?&token={}".format(config["token"])
    return url


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


async def _get_rasa_nlu_version(config):
    """Get Rasa NLU version data"""
    async with aiohttp.ClientSession(trust_env=True) as session:
        url = config.get("url", RASANLU_DEFAULT_URL) + "/version"
        try:
            resp = await session.get(url)
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


async def has_compatible_version_rasanlu(config):
    """Check if Rasa NLU is compatible with the API we implement"""
    _LOGGER.debug(_("Checking Rasa NLU version."))
    json_object = await _get_rasa_nlu_version(config)
    version = json_object["version"]
    minimum_compatible_version = json_object["minimum_compatible_version"]
    # Make sure we don't run against a 1.x.x Rasa NLU because it has a different API
    if int(minimum_compatible_version[0:1]) >= 2:
        _LOGGER.debug(_("Rasa NLU version {}.".format(version)))
        return True

    _LOGGER.error(
        _(
            "Incompatible Rasa NLU version ({}). Use Rasa Version >= 2.X.X.".format(
                version
            )
        )
    )
    return False


async def _load_model(config):
    """Load model from the filesystem of the Rasa NLU environment"""
    async with aiohttp.ClientSession(trust_env=True) as session:
        headers = {}
        data = {
            "model_file": "{}/{}".format(
                config.get("models-path", RASANLU_DEFAULT_MODELS_PATH),
                config["model_filename"],
            ),
        }
        url = config.get("url", RASANLU_DEFAULT_URL) + "/model"
        if "token" in config:
            url += "?token={}".format(config["token"])
        try:
            resp = await session.put(url, data=json.dumps(data), headers=headers)
        except aiohttp.client_exceptions.ClientConnectorError:
            _LOGGER.error(_("Unable to connect to Rasa NLU."))
            return None
        if resp.status == 204:
            result = await resp.json()
        else:
            result = await resp.text()
            _LOGGER.error(_("Bad Rasa NLU response - %s."), result)

        return result


async def _is_model_loaded(config):
    """Check whether the model is loaded in Rasa NLU"""
    async with aiohttp.ClientSession(trust_env=True) as session:
        url = config.get("url", RASANLU_DEFAULT_URL) + "/status"
        if "token" in config:
            url += "?token={}".format(config["token"])
        try:
            resp = await session.get(await _build_status_url(config))
        except aiohttp.client_exceptions.ClientConnectorError:
            _LOGGER.error(_("Unable to connect to Rasa NLU."))
            return None
        if resp.status == 200:
            result = await resp.json()
            if result["model_file"].find(config["model_filename"]):
                return True
        return False


async def train_rasanlu(config, skills):
    """Train a Rasa NLU model based on the loaded skills."""
    train = config.get("train", RASANLU_DEFAULT_TRAIN_MODEL)
    if train is False:
        _LOGGER.info(_("Skipping Rasa NLU model training as specified in the config."))
        return False

    _LOGGER.info(_("Starting Rasa NLU training."))
    intents = await _get_all_intents(skills)
    if intents is None:
        _LOGGER.warning(_("No intents found, skipping training."))
        return False

    """
    TODO: think about how to correlate intent with trained model
          so we can just load the model without training it again if it wasn't changed
    """

    async with aiohttp.ClientSession(trust_env=True) as session:
        _LOGGER.info(_("Now training the model. This may take a while..."))

        url = await _build_training_url(config)

        headers = {"Content-Type": "application/x-yaml"}

        try:
            training_start = arrow.now()
            resp = await session.post(url, data=intents, headers=headers)
        except aiohttp.client_exceptions.ClientConnectorError:
            _LOGGER.error(_("Unable to connect to Rasa NLU, training failed."))
            return False

        if resp.status == 200:
            if (
                resp.content_type == "application/x-tar"
                and resp.content_disposition.type == "attachment"
            ):
                time_taken = (arrow.now() - training_start).total_seconds()
                _LOGGER.info(
                    _("Rasa NLU training completed in %s seconds."), int(time_taken)
                )
                config["model_filename"] = resp.content_disposition.filename
                # close the connection and don't retrieve the model tar
                # because using it is currently not implemented
                resp.close()

                """
                model_path = "/tmp/{}".format(resp.content_disposition.filename)
                try:
                    output_file = open(model_path,"wb")
                    data = await resp.read()
                    output_file.write(data)
                    output_file.close()
                    _LOGGER.debug("Rasa taining model file saved to {}", model_path)
                except:
                    _LOGGER.error("Cannot save rasa taining model file to {}", model_path)
                """

                await _load_model(config)
                # Check if the current trained model is loaded
                if await _is_model_loaded(config):
                    _LOGGER.info(_("Successfully loaded Rasa NLU model."))
                else:
                    _LOGGER.error(_("Failed getting Rasa NLU server status."))
                    return False

                # Check if we will get a valid response from Rasa
                await call_rasanlu("", config)
                return True

        _LOGGER.error(_("Bad Rasa NLU response - %s."), await resp.text())
        _LOGGER.error(_("Rasa NLU training failed."))
        return False


async def call_rasanlu(text, config):
    """Call the Rasa NLU api and return the response."""
    async with aiohttp.ClientSession(trust_env=True) as session:
        headers = {}
        data = {"text": text}
        url = config.get("url", RASANLU_DEFAULT_URL) + "/model/parse"
        if "token" in config:
            url += "?&token={}".format(config["token"])
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
                            if "confidence_entity" in entity:
                                message.update_entity(
                                    entity["entity"],
                                    entity["value"],
                                    entity["confidence_entity"],
                                )
                            elif "extractor" in entity:
                                message.update_entity(
                                    entity["entity"],
                                    entity["value"],
                                    entity["extractor"],
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
