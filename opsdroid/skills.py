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

def match_apiai(action):
    """Return apiai match decorator."""
    def matcher(func):
        """Add decorated function to skills list for apiai matching."""
        for opsdroid in OpsDroid.instances:
            opsdroid.skills.append({"apiai": action, "skill": func})
        return func
    return matcher
