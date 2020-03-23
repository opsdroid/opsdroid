"""A helper function for parsing and executing crontab skills."""
import time
import asyncio
import logging

import arrow
import pycron


_LOGGER = logging.getLogger(__name__)


async def parse_crontab(opsdroid):
    """Parse all crontab skills against the current time."""
    while opsdroid.eventloop.is_running():
        await asyncio.sleep(60 - arrow.now().time().second)
        _LOGGER.debug(_("Running crontab skills at %s."), time.asctime())
        for skill in opsdroid.skills:
            for matcher in skill.matchers:
                if "crontab" in matcher:
                    if matcher["timezone"] is not None:
                        timezone = matcher["timezone"]
                    else:
                        timezone = opsdroid.config.get("timezone", "UTC")
                    if pycron.is_now(matcher["crontab"], arrow.now(tz=timezone)):
                        await opsdroid.run_skill(skill, skill.config, None)
