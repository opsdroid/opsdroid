"""A helper function for parsing and executing wit.ai skills."""

import logging
import json
import unicodedata

import aiohttp

_LOGGER = logging.getLogger(__name__)


async def train_rasanlu(config, skills):
    """Train a Rasa NLU model based on the loaded skills."""
    # TODO: Check if the model has already been trained and skip if so.
    _LOGGER.info("Training a new Rasa NLU model. This may take a while...")
    intents = [skill["intents"] for skill in skills if skill["intents"] is not None]
    if not len(intents):
        _LOGGER.warning("No intents found, skipping training.")
        return
    intents = "\n\n".join(intents)
    intents = unicodedata.normalize("NFKD", intents).encode('ascii')
    async with aiohttp.ClientSession() as session:
        url = config.get("url", 'http://localhost:5000') \
            + "/train?project={}".format(config["project"])
        try:
            resp = await session.post(url, data=intents)
        except aiohttp.client_exceptions.ClientConnectorError:
            _LOGGER.error("Unable to connect to Rasa NLU, training failed.")
            return
        if resp.status == 200:
            result = await resp.json()
            if "info" in result and "new model trained" in result["info"]:
                _LOGGER.info("Rasa NLU training complete.")
                config["model"] = result["info"].split(":")[1].strip()
                _LOGGER.info("Initialising Rasa NLU model. "
                             "This might also take a while...")
                result = await call_rasanlu("", config)
                if result is None:
                    _LOGGER.error("Initialisation failed, training failed..")
                else:
                    _LOGGER.info("Initialisation complete.")
                return
            else:
                _LOGGER.debug(result)
        else:
            _LOGGER.error("Bad Rasa NLU response - %s", await resp.text())
        _LOGGER.error("Rasa NLU training failed.")


async def call_rasanlu(text, config):
    """Call the Rasa NLU api and return the response."""
    async with aiohttp.ClientSession() as session:
        headers = {
        }
        data = {
            "q": text,
            "project": config.get("project", "default"),
            "model": config.get("model", "fallback")
        }
        if "token" in config:
            data["token"] = config["token"]
        url = config.get("url", 'http://localhost:5000') + "/parse"
        try:
            resp = await session.post(url, data=json.dumps(data), headers=headers)
        except aiohttp.client_exceptions.ClientConnectorError:
            _LOGGer.error("Unable to connect to Rasa NLU")
            return None
        if resp.status == 200:
            result = await resp.json()
            _LOGGER.debug("Rasa NLU response - %s", json.dumps(result))
        else:
            result = await resp.text()
            _LOGGER.error("Bad Rasa NLU response - %s", result)

        return result


async def parse_rasanlu(opsdroid, message, config):
    """Parse a message against all Rasa NLU skills."""
    matched_skills = []
    try:
        result = await call_rasanlu(message.text, config)
    except aiohttp.ClientOSError:
        _LOGGER.error("No response from Rasa NLU, check your network.")
        return matched_skills

    if result == 'unauthorized':
        _LOGGER.error("Rasa NLU error - Unauthorised request. Check your 'token'.")
        return matched_skills

    if 'intent' not in result or result['intent'] is None:
        _LOGGER.error("Rasa NLU error - No intent found. Did you "
                      "forget to create one?")
        return matched_skills

    confidence = result['intent']['confidence']
    if "min-score" in config and confidence < config['min-score']:
        _LOGGER.info("Rasa NLU score lower than min-score")
        return matched_skills

    if result:
        for skill in opsdroid.skills:
            if "rasanlu_intent" in skill:
                if skill['rasanlu_intent'] == result['intent']['name']:
                    message.rasanlu = result
                    matched_skills.append({
                        "score": confidence,
                        "skill": skill["skill"],
                        "config": skill["config"],
                        "message": message
                    })
    return matched_skills
