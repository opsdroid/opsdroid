"""A helper function for training, parsing and executing Snips NLU skills."""

import logging
import unicodedata
import requests
import os

from hashlib import sha256


from snips_nlu import SnipsNLUEngine

_LOGGER = logging.getLogger(__name__)
model = None

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
    """Iniialising the model into memory."""
    _LOGGER.info(_("Initialising Snips NLU model."))
    global model
    model = SnipsNLUEngine(config=config)
     
    return True

async def train_snipsnlu(config, skills):
    """Train a Snips NLU model based on the loaded skills."""
    _LOGGER.info(_("Starting Snips NLU training."))
    global model
    intents = await _get_all_intents(skills)
    if intents is None:
        _LOGGER.warning(_("No intents found, skipping training."))
        return False

    config["model"] = await _get_intents_fingerprint(intents)
    if config["model"] in await _get_existing_models(config):
        _LOGGER.info(_("This model already exists, skipping training..."))
        await _init_model(config)
        return True
    
    _LOGGER.info(_("Now training the model. This may take a while..."))
    url = "https://github.com/snipsco/snips-nlu/blob/master/sample_datasets/lights_dataset.json"
    directory = os.getcwd()
    file = os.path.join(getcwd(),'lights_dataset.json')
    r = requests.get(url)
    model = model.fit(file)
    return True

    
