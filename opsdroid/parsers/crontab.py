"""A helper function for parsing and executing crontab skills."""

import asyncio
import logging

import arrow
import pycron


_LOGGER = logging.getLogger(__name__)


async def parse_crontab(opsdroid):
    """Parse all crontab skills against the current time."""
    while opsdroid.eventloop.is_running():
        await asyncio.sleep(60 - arrow.now().time().second)
        _LOGGER.debug(_("Running crontab skills"))
        for skill in opsdroid.skills:
            if "crontab" in skill:
                if skill["timezone"] is not None:
                    timezone = skill["timezone"]
                else:
                    timezone = opsdroid.config.get("timezone", "UTC")
                if pycron.is_now(skill["crontab"], arrow.now(tz=timezone)):
                    await opsdroid.run_skill(skill["skill"],
                                             skill["config"],
                                             None)
