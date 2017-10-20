"""A helper function for parsing and executing AWS Lex utterances."""

import logging
import aiobotocore

_LOGGER = logging.getLogger(__name__)


async def call_lex(message, config):
    """Call the Lex api and return the response."""
    session = aiobotocore.get_session()
    async with session.create_client(
        'lex-runtime',
        region_name=config['region'],
        aws_access_key_id=config['access_id'],
        aws_secret_access_key=config['access_secret']
    ) as client:
        response = client.post_text(
            botName=config['lex_bot'],
            botAlias=config['lex_alias'],
            userId=config['lex_user'],
            inputText=message
        )
        return response


async def parse_lex(opsdroid, message, config):
    """Parse a message for Lex processing."""
    # pylint: disable=broad-except
    # We want to catch all exceptions coming from a skill module and not
    # halt the application. If a skill throws an exception it just doesn't
    # give a response to the user, so an error response should be given.
    if 'access_id' and 'access_secret' in config:
        try:
            result = await call_lex(message, config)
        except aiobotocore.ClientError:
            _LOGGER.error("Boto client error")
            return
        _LOGGER.debug(result)

        if result["status"]["code"] >= 300:
            _LOGGER.error("lex error - " +
                          str(result["status"]["code"]) + " " +
                          result["status"]["errorType"])
            return

        if result:
            for skill in opsdroid.skills:
                if "lex_intent" in skill:
                    if ("intentName" in result and skill["lex_intent"] in
                            result["intentName"]):
                            message.lex = result
                            try:
                                await skill["skill"](
                                    opsdroid,
                                    skill["config"],
                                    message
                                )
                            except Exception:
                                await message.respond(
                                    "Whoops there has been an error")
                                await message.respond(
                                    "Check the log for details")
                                _LOGGER.exception("Exception when parsing '" +
                                                  message.text +
                                                  "' against skill '" +
                                                  result["lex_intent"] + "'")
    else:
        _LOGGER.error("Missing access_id and/or access_secret")
