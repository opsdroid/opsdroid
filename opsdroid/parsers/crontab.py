"""A helper function for parsing and executing crontab skills."""

import asyncio
import logging

import arrow
import pycron


_LOGGER = logging.getLogger(__name__)


async def parse_crontab(opsdroid):
    """Parse all crontab skills against the current time."""
    # pylint: disable=broad-except
    # We want to catch all exceptions coming from a skill module and not
    # halt the application. If a skill throws an exception it just doesn't
    # give a response to the user, so an error response should be given.
    while opsdroid.eventloop.is_running():
        await asyncio.sleep(60 - arrow.now().time().second)
        _LOGGER.debug("Running crontab skills")
        for skill in opsdroid.skills:
            if "crontab" in skill:
                if skill["timezone"] is not None:
                    timezone = skill["timezone"]
                else:
                    timezone = opsdroid.config.get("timezone", "UTC")
                if pycron.is_now(skill["crontab"], arrow.now(tz=timezone)):
                    try:
                        await skill["skill"](opsdroid, skill["config"], None)
                    except Exception:
                        _LOGGER.exception(
                            "Exception when executing cron skill.")
