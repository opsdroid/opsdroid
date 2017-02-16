"""Decorator functions to use when creating skill modules."""

import logging

from opsdroid.helper import get_opsdroid
from opsdroid.web import Web


_LOGGER = logging.getLogger(__name__)


def match_regex(regex):
    """Return regex match decorator."""
    def matcher(func):
        """Add decorated function to skills list for regex matching."""
        opsdroid = get_opsdroid()
        opsdroid.skills.append({"regex": regex, "skill": func,
                                "config":
                                opsdroid.loader.current_import_config})
        return func
    return matcher


def match_apiai_action(action):
    """Return apiai action match decorator."""
    def matcher(func):
        """Add decorated function to skills list for apiai matching."""
        opsdroid = get_opsdroid()
        opsdroid.skills.append({"apiai_action": action, "skill": func,
                                "config":
                                opsdroid.loader.current_import_config})
        return func
    return matcher


def match_apiai_intent(intent):
    """Return apiai intent match decorator."""
    def matcher(func):
        """Add decorated function to skills list for apiai matching."""
        opsdroid = get_opsdroid()
        opsdroid.skills.append({"apiai_intent": intent, "skill": func,
                                "config":
                                opsdroid.loader.current_import_config})
        return func
    return matcher


def match_crontab(crontab):
    """Return crontab match decorator."""
    def matcher(func):
        """Add decorated function to skills list for crontab matching."""
        opsdroid = get_opsdroid()
        opsdroid.skills.append({"crontab": crontab, "skill": func,
                                "config":
                                opsdroid.loader.current_import_config})
        return func
    return matcher


def match_webhook(webhook):
    """Return webhook match decorator."""
    def matcher(func):
        """Add decorated function to skills list for webhook matching."""
        opsdroid = get_opsdroid()
        config = opsdroid.loader.current_import_config
        opsdroid.skills.append({"webhook": webhook, "skill": func,
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
