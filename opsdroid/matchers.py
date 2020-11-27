"""Decorator functions to use when creating skill modules."""

import logging

from opsdroid.const import REGEX_PARSE_SCORE_FACTOR
from opsdroid.helper import add_skill_attributes

_LOGGER = logging.getLogger(__name__)


def match_event(event_type, **kwargs):
    """Return event type matcher.

    Decorator that calls skill based on passed event_type.

    Args:
        event_type (str): opsdroidstarted, message, typing, reaction, file, image
        **kwargs (dict): arbitrary kwargs to be added to the event matcher
    Returns:
        Decorated function

    """

    def matcher(func):
        """Add decorated function to list for event matching."""
        func = add_skill_attributes(func)
        func.matchers.append({"event_type": dict(type=event_type, **kwargs)})
        return func

    return matcher


def match_regex(
    regex, case_sensitive=True, matching_condition="match", score_factor=None
):
    """Return regex match decorator.

    Decorator used to handle regex matching in skills. Decorated function will be called if regex
    string matches. Matching can be customized based on the matching condition passed.

    Args:
        regex (str): Regex expression as a string.
        case_sensitive (bool): Flag to check for case sensitive matching, defaults to True.
        matching_condition (str): Type of matching to be applied, can be "search", "match" or
            "fullmatch"
        score_factor (float): Score multiplier used by Rasa NLU skills

    Returns:
        Decorated function

    """

    def matcher(func):
        """Add decorated function to skills list for regex matching."""
        func = add_skill_attributes(func)
        func.matchers.append(
            {
                "regex": {
                    "expression": regex,
                    "case_sensitive": case_sensitive,
                    "matching_condition": matching_condition,
                    "score_factor": score_factor or REGEX_PARSE_SCORE_FACTOR,
                }
            }
        )
        return func

    return matcher


def match_parse(
    format_str, case_sensitive=True, matching_condition="match", score_factor=None
):
    """Return parse match decorator.

    Decorator that matches the message from the user against a string with python format syntax.
    If the string matches then the function is called. matching_condition can be set to customize
    if string match should match format_str only at the beginning of input string or match in the
    first location where format_str is found.

    Args:
        format_str (str): A python format string to be matched.
        case_sensitive (bool):  Boolean flag to check if matching should be case sensitive.
        matching_condition (str): Type of matching to be applied, can be "match" or "search"
        score_factor (float): Score multiplier used by Rasa NLU skills

    Returns:
        Decorated function

    """

    def matcher(func):
        """Add decorated function to skills list for parse matching."""
        func = add_skill_attributes(func)
        func.matchers.append(
            {
                "parse_format": {
                    "expression": format_str,
                    "case_sensitive": case_sensitive,
                    "matching_condition": matching_condition,
                    "score_factor": score_factor or REGEX_PARSE_SCORE_FACTOR,
                }
            }
        )
        return func

    return matcher


def match_dialogflow_action(action):
    """Return Dialogflow action match decorator.

    Decorator that calls a function on any Dialogflow intent with a specified action.

    Args:
        action (str): Dialogflow action

    Returns:
        Decorated Function

    """

    def matcher(func):
        """Add decorated function to skills list for Dialogflow matching."""
        func = add_skill_attributes(func)
        func.matchers.append({"dialogflow_action": action})
        return func

    return matcher


def match_dialogflow_intent(intent):
    """Return Dialogflow intent match decorator.

    Decorator that calls a function on specific Diaglogflow API intents.

    Args:
        intent (str): Dialogflow intent name

    Returns:
        Decorated Function

    """

    def matcher(func):
        """Add decorated function to skills list for Dialogflow matching."""
        func = add_skill_attributes(func)
        func.matchers.append({"dialogflow_intent": intent})
        return func

    return matcher


def match_luisai_intent(intent):
    """Return luis.ai intent match decorator.

    Decorator that calls a function on specific luis.ai intents.

    Args:
        intent (str): luis.ai intent name

    Returns:
        Decorated Function

    """

    def matcher(func):
        """Add decorated function to skills list for luisai matching."""
        func = add_skill_attributes(func)
        func.matchers.append({"luisai_intent": intent})
        return func

    return matcher


def match_rasanlu(intent):
    """Return Rasa NLU intent match decorator.

    Decorator that calls a function on specific Rasa NLU intents.

    Args:
        intent (str): Rasa NLU intent name

    Returns:
        Decorated Function

    """

    def matcher(func):
        """Add decorated function to skills list for Rasa NLU matching."""
        func = add_skill_attributes(func)
        func.matchers.append({"rasanlu_intent": intent})
        return func

    return matcher


def match_recastai(intent):
    """Return Recast.ai intent match decorator.

    Decorator that calls a function on specific Recast.ai intents.

    Args:
        intent (str): Recast.ai intent name

    Returns:
        Decorated Function

    """

    def matcher(func):
        """Add decorated function to skills list for recastai matching."""
        func = add_skill_attributes(func)
        func.matchers.append({"sapcai_intent": intent})
        return func

    _LOGGER.warning(
        _(
            "Recast.AI is now called SAP Conversational AI, this matcher will stop working in the future. "
            "Use match_sapcai instead."
        )
    )
    return matcher


def match_sapcai(intent):
    """Return SAP Conversational AI intent match decorator.

    Decorator that calls a function on specific SAP Conversational AI intents.

    Args:
        intent (str): SAP Conversational AI intent name

    Returns:
        Decorated Function

    """

    def matcher(func):
        """Add decorated function to skills list for SAPCAI matching."""
        func = add_skill_attributes(func)
        func.matchers.append({"sapcai_intent": intent})
        return func

    return matcher


def match_watson(intent):
    """Return IBM Watson intent match decorator.

    Decorator that calls a function on specific IBM Watson intents.

    Args:
        intent (str): IBM Watson intent name

    Returns:
        Decorated Function

    """

    def matcher(func):
        """Add decorated function to skills list for watson matching."""
        func = add_skill_attributes(func)
        func.matchers.append({"watson_intent": intent})
        return func

    return matcher


def match_witai(intent):
    """Return wit.ai intent match decorator.

    Decorator that calls a function on specific wit.ai intents.

    Args:
        intent (str): wit.ai intent name

    Returns:
        Decorated Function

    """

    def matcher(func):
        """Add decorated function to skills list for witai matching."""
        func = add_skill_attributes(func)
        func.matchers.append({"witai_intent": intent})
        return func

    return matcher


def match_crontab(crontab, timezone=None):
    """Return crontab match decorator.

    Decorator that, after enabling crontab skill config, calls a function when cron timing interval
    passes.

    Args:
        crontab (str): cron timing string
        timezone (str): timezone string, defaults to root configuration

    Returns:
        Decorated Function

    """

    def matcher(func):
        """Add decorated function to skills list for crontab matching."""
        func = add_skill_attributes(func)
        func.matchers.append({"crontab": crontab, "timezone": timezone})
        return func

    return matcher


def match_webhook(webhook):
    """Return webhook match decorator.

    Decorator that calls the decorated function when a POST is sent to
    http://localhost:8080/skill/exampleskill/<webhook>. Does not need a message as input.

    Args:
        webhook(str): webhook url

    Returns:
        Decorated Function

    """

    def matcher(func):
        """Add decorated function to skills list for webhook matching."""
        func = add_skill_attributes(func)
        func.matchers.append({"webhook": webhook})

        return func

    return matcher


def match_always(func=None):
    """Return always match decorator.

    Decorator that parses every message as it is always running, it does not be need to be
    configured explicitly.

    Returns:
        Decorated Function

    """

    def matcher(func):
        """Add decorated function to skills list for always matching."""
        func = add_skill_attributes(func)
        func.matchers.append({"always": True})
        return func

    # Allow for decorator with or without parenthesis as there are no args.
    if callable(func):
        return matcher(func)
    return matcher


def match_catchall(func=None, messages_only=False):
    """Return catch-all match decorator.

    Decorator that runs the function only if no other skills were matched for a message

    Args:
        messages_only(bool): Whether to match only on messages, or on all events. Defaults to False.

    Returns:
        Decorated Function

    """

    def matcher(func):
        """Add decorated function to skills list for catch-all matching."""
        func = add_skill_attributes(func)
        func.matchers.append({"catchall": True, "messages_only": messages_only})
        return func

    # Allow for decorator with or without parenthesis as there are no args.
    if callable(func):
        return matcher(func)
    return matcher
