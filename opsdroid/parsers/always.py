"""A helper function for parsing and executing always skills."""

import logging


_LOGGER = logging.getLogger(__name__)


async def parse_always(opsdroid, message):
    """Parse a message always."""
    # pylint: disable=broad-except
    # We want to catch all exceptions coming from a skill module and not
    # halt the application. If a skill throws an exception it just doesn't
    # give a response to the user, so an error response should be given.
    for skill in opsdroid.skills:
        if "always" in skill and skill["always"]:
            try:
                await skill["skill"](opsdroid, skill["config"], message)
            except Exception:
                await message.respond(
                    "Whoops there has been an error")
                await message.respond(
                    "Check the log for details")
                _LOGGER.exception("Exception when parsing '" +
                                  message.text + "'")
