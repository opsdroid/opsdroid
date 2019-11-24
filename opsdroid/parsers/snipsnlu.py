"""A helper function for training, parsing and executing Snips NLU skills."""

import logging
import json
import unicodedata

from hashlib import sha256

import os
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
    pass

async def _get_existing_models(config):
    """Get a list of models already trained in the Snips NLU project."""
    project = config.get("project", SNIPSNLU_DEFAULT_PROJECT)
    try:
        resp = await _build_dir(config)
        os.system("cd {}").format(resp)
        result = os.popen('ls').read()
        result = list(result.split("\n"))
        if project in result:
            project_models = result[project]
            return project_models["available_models"]
    except OSError as e:
        _LOGGER.error(_("Directory not build"))
        
    return []
        
