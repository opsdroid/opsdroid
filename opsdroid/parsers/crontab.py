"""A helper function for parsing and executing crontab skills."""

import logging
import asyncio
from datetime import datetime

import pycron


async def parse_crontab(opsdroid):
    """Parse all crontab skills against the current time."""
    # pylint: disable=broad-except
    # We want to catch all exceptions coming from a skill module and not
    # halt the application. If a skill throws an exception it just doesn't
    # give a response to the user, so an error response should be given.
    while opsdroid.eventloop.is_running():
        await asyncio.sleep(60 - datetime.now().time().second)
        logging.debug("Running crontab skills")
        for skill in opsdroid.skills:
            if "crontab" in skill and pycron.is_now(skill["crontab"]):
                try:
                    await skill["skill"](opsdroid, None)
                except Exception:
                    logging.exception("Exception when executing cron skill.")
