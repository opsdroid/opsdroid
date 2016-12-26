"""A helper function for parsing and executing regex skills."""

import logging
import re


async def parse_regex(opsdroid, message):
    """Parse a message against all regex skills."""
    # pylint: disable=broad-except
    # We want to catch all exceptions coming from a skill module and not
    # halt the application. If a skill throws an exception it just doesn't
    # give a response to the user, so an error response should be given.
    for skill in opsdroid.skills:
        if "regex" in skill:
            regex = re.match(skill["regex"], message.text)
            if regex:
                message.regex = regex
                try:
                    await skill["skill"](opsdroid, message)
                except Exception:
                    await message.respond(
                        "Whoops there has been an error")
                    await message.respond(
                        "Check the log for details")
                    logging.exception("Exception when parsing '" +
                                      message.text +
                                      "' against skill '" +
                                      skill["regex"] + "'")
