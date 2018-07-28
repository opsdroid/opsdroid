"""Decorator functions to use when creating skill modules."""

import logging

from opsdroid.helper import get_opsdroid
from opsdroid.web import Web


_LOGGER = logging.getLogger(__name__)


def match_regex(regex, case_sensitive=True):
    """Return regex match decorator."""
    def matcher(func):
        """Add decorated function to skills list for regex matching."""
        opsdroid = get_opsdroid()
        if opsdroid:
            config = opsdroid.loader.current_import_config
            regex_setup = {
                "expression": regex,
                "case_sensitive": case_sensitive
            }
            opsdroid.skills.append({"regex": regex_setup,
                                    "skill": func,
                                    "config": config})
        return func
    return matcher


def match_apiai_action(action):
    """Return Dialogflow action match decorator."""
    def matcher(func):
        """Add decorated function to skills list for Dialogflow matching."""
        opsdroid = get_opsdroid()
        if opsdroid:
            config = opsdroid.loader.current_import_config
            opsdroid.skills.append({"dialogflow_action": action,
                                    "skill": func,
                                    "config": config})
        return func
    _LOGGER.warning(_("Api.ai is now called Dialogflow, this matcher "
                      "will stop working in the future. "
                      "Use match_dialogflow_action instead."))
    return matcher


def match_apiai_intent(intent):
    """Return Dialogflow intent match decorator."""
    def matcher(func):
        """Add decorated function to skills list for Dialogflow matching."""
        opsdroid = get_opsdroid()
        if opsdroid:
            config = opsdroid.loader.current_import_config
            opsdroid.skills.append({"dialogflow_intent": intent,
                                    "skill": func,
                                    "config": config})
        return func
    _LOGGER.warning(_("Api.ai is now called Dialogflow, this matcher "
                      "will stop working in the future. "
                      "Use match_dialogflow_intent instead."))
    return matcher


def match_dialogflow_action(action):
    """Return Dialogflowi action match decorator."""
    def matcher(func):
        """Add decorated function to skills list for Dialogflow matching."""
        opsdroid = get_opsdroid()
        if opsdroid:
            config = opsdroid.loader.current_import_config
            opsdroid.skills.append({"dialogflow_action": action,
                                    "skill": func,
                                    "config": config})
        return func
    return matcher


def match_dialogflow_intent(intent):
    """Return Dialogflow intent match decorator."""
    def matcher(func):
        """Add decorated function to skills list for Dialogflow matching."""
        opsdroid = get_opsdroid()
        if opsdroid:
            config = opsdroid.loader.current_import_config
            opsdroid.skills.append({"dialogflow_intent": intent,
                                    "skill": func,
                                    "config": config})
        return func
    return matcher


def match_luisai_intent(intent):
    """Return luisai intent match decorator."""
    def matcher(func):
        """Add decorated function to skills list for luisai matching."""
        opsdroid = get_opsdroid()
        if opsdroid:
            config = opsdroid.loader.current_import_config
            opsdroid.skills.append({"luisai_intent": intent,
                                    "skill": func,
                                    "config": config})
        return func
    return matcher


def match_rasanlu(intent):
    """Return Rasa NLU intent match decorator."""
    def matcher(func):
        """Add decorated function to skills list for Rasa NLU matching."""
        opsdroid = get_opsdroid()
        if opsdroid:
            config = opsdroid.loader.current_import_config
            opsdroid.skills.append({"rasanlu_intent": intent,
                                    "skill": func,
                                    "config": config})
        return func
    return matcher


def match_recastai(intent):
    """Return recastai intent match decorator."""
    def matcher(func):
        """Add decorated function to skills list for recastai matching."""
        opsdroid = get_opsdroid()
        if opsdroid:
            config = opsdroid.loader.current_import_config
            opsdroid.skills.append({"recastai_intent": intent,
                                    "skill": func,
                                    "config": config})
        return func
    return matcher


def match_witai(intent):
    """Return witai intent match decorator."""
    def matcher(func):
        """Add decorated function to skills list for witai matching."""
        opsdroid = get_opsdroid()
        if opsdroid:
            config = opsdroid.loader.current_import_config
            opsdroid.skills.append({"witai_intent": intent,
                                    "skill": func,
                                    "config": config})
        return func
    return matcher


def match_crontab(crontab, timezone=None):
    """Return crontab match decorator."""
    def matcher(func):
        """Add decorated function to skills list for crontab matching."""
        opsdroid = get_opsdroid()
        if opsdroid:
            config = opsdroid.loader.current_import_config
            opsdroid.skills.append({"crontab": crontab,
                                    "skill": func,
                                    "config": config,
                                    "timezone": timezone})
        return func
    return matcher


def match_webhook(webhook):
    """Return webhook match decorator."""
    def matcher(func):
        """Add decorated function to skills list for webhook matching."""
        opsdroid = get_opsdroid()
        if opsdroid:
            config = opsdroid.loader.current_import_config
            opsdroid.skills.append({"webhook": webhook,
                                    "skill": func,
                                    "config": config})

            async def wrapper(req, opsdroid=opsdroid, config=config):
                """Wrap up the aiohttp handler."""
                _LOGGER.info("Running skill %s via webhook", webhook)
                opsdroid.stats["webhooks_called"] = \
                    opsdroid.stats["webhooks_called"] + 1
                await func(opsdroid, config, req)
                return Web.build_response(200, {"called_skill": webhook})

            opsdroid.web_server.web_app.router.add_post(
                "/skill/{}/{}".format(config["name"], webhook), wrapper)
            opsdroid.web_server.web_app.router.add_post(
                "/skill/{}/{}/".format(config["name"], webhook), wrapper)

        return func
    return matcher


def match_always(func=None):
    """Return always match decorator."""
    def matcher(func):
        """Add decorated function to skills list for always matching."""
        opsdroid = get_opsdroid()
        if opsdroid:
            config = opsdroid.loader.current_import_config
            opsdroid.skills.append({"always": True,
                                    "skill": func,
                                    "config": config})
        return func

    # Allow for decorator with or without parenthesis as there are no args.
    if callable(func):
        return matcher(func)
    return matcher
