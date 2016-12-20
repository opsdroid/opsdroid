"""Decorator functions to use when creating skill modules."""

from opsdroid.core import OpsDroid


def match_regex(regex):
    """Return regex match decorator."""
    def matcher(func):
        """Add decorated function to skills list for regex matching."""
        for opsdroid in OpsDroid.instances:
            opsdroid.skills.append({"regex": regex, "skill": func})
        return func
    return matcher


def match_apiai_action(action):
    """Return apiai action match decorator."""
    def matcher(func):
        """Add decorated function to skills list for apiai matching."""
        for opsdroid in OpsDroid.instances:
            opsdroid.skills.append({"apiai_action": action, "skill": func})
        return func
    return matcher


def match_apiai_intent(intent):
    """Return apiai intent match decorator."""
    def matcher(func):
        """Add decorated function to skills list for apiai matching."""
        for opsdroid in OpsDroid.instances:
            opsdroid.skills.append({"apiai_intent": intent, "skill": func})
        return func
    return matcher


def match_crontab(crontab):
    """Return crontab match decorator."""
    def matcher(func):
        """Add decorated function to skills list for crontab matching."""
        for opsdroid in OpsDroid.instances:
            opsdroid.skills.append({"crontab": crontab, "skill": func})
        return func
    return matcher
