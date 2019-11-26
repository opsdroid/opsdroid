"""A helper function for training, parsing and executing Snips NLU skills."""

import logging
import json
import unicodedata

from hashlib import sha256

import os
from snips_nlu import SnipsNLUEngine
from os import path
import arrow

from opsdroid.const import SNIPSNLU_DEFAULT_DIR, SNIPSNLU_DEFAULT_PROJECT

_LOGGER = logging.getLogger(__name__)


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


async def _init_model(config):
    """Make a request to force Snips NLU to load the model into memory."""
    _LOGGER.info(_("Initialising Snips NLU model."))

    initialisation_start = arrow.now()
    result = await call_snipsnlu("", config)

    if result is None:
        _LOGGER.error(_("Initialisation failed, training failed.."))
        return False

    time_taken = int((arrow.now() - initialisation_start).total_seconds())
    _LOGGER.info(_("Initialisation complete in %s seconds."), time_taken)

    return True


async def _build_dir(config):
    directory = config.get("directory", SNIPSNLU_DEFAULT_DIR)
    if path.exists(directory):
        return directory
    else:
        os.system("mkdir "+directory)
        return directory
    
async def _get_existing_models(config):
    """Get a list of models already trained in the Snips NLU."""
    try:
        resp = await _build_dir(config)
        result = os.popen('ls '+resp).read()
        result = list(result.split("\n"))
        if len(result) != 0:
            return result
    except OSError as e:
        _LOGGER.error(_("Directory not build"))
        
    return []

async def train_rasanlu(config, skills):
    """Train a Snips NLU model based on the loaded skills."""
    _LOGGER.info("Starting Snips NLU training.")
    intents = await _get_all_intents(skills)
    if intents is None:
        _LOGGER.warning("No intents found, skipping training.")
        return False

    config["model"] = await _get_intents_fingerprint(intents)
    if config["model"] in await _get_existing_models(config):
        _LOGGER.info("This model already exists, skipping training...")
        await _init_model(config)
        return True
    _LOGGER.info("Now training the model. This may take a while...")
    directory = _build_dir(config)

    training_start = arrow.now()
    engine = SnipsNLUEngine(config)
    engine.fit(intents)
    engine.persist("{}\{}".format(directory, config["model"]))
    time_taken = (arrow.now() - training_start).total_seconds()
    _LOGGER.info("Rasa NLU training completed in %s seconds.",int(time_taken))
    return True
        
async def call_snipsnlu(text, config):
    """Call the Snips NLU api and return the response."""
    model = config.get("model", "fallback")
    directory = _build_dir()
    
    loaded_engine = SnipsNLUEngine.from_path("{}\{}".format(directory, model))
    result = loaded_engine.parse(text)
    return result

async def parse_snipsnlu(opsdroid, skills, message, config):
    """Parse a message against all Snips NLU skills."""
    matched_skills = []
    
    result = await call_snipsnlu(message.text, config)
    if result:
        for skill in opsdroid.skills:
            if "rasanlu_intent" in skill:
                if skill['rasanlu_intent'] == result['intent']['name']:
                    message.rasanlu = result
                    matched_skills.append({
                        "skill": skill["skill"],
                        "config": skill["config"],
                        "message": message
                    })

    return matched_skills