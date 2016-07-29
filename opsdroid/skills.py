"""Decorator functions to use when creating skill modules."""

from opsdroid.core import OpsDroid


def match_regex(regex):
    """Return regex match decorator."""
    def matcher(func):
        """Add decorated function to skills list for regex matching."""
        for opsdroid in OpsDroid.instances:
            opsdroid.load_regex_skill(regex, func)
        return func
    return matcher
