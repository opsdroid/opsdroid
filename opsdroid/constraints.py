"""Decorator functions to use when creating skill modules.

These decorators are for specifying when a skill should not be called despite
having a matcher which matches the current message.
"""

import logging

from opsdroid.helper import add_skill_attributes, negate


_LOGGER = logging.getLogger(__name__)


def constrain_rooms(rooms, invert=False):
    """Return room constraint decorator."""

    def constraint_decorator(func):
        """Add room constraint to skill."""

        def constraint_callback(message, rooms=rooms):
            """Check if the room is correct."""
            return message.target in rooms

        func = add_skill_attributes(func)
        if invert:
            func.constraints.append(negate(constraint_callback))
        else:
            func.constraints.append(constraint_callback)
        return func

    return constraint_decorator


def constrain_users(users, invert=False):
    """Return user constraint decorator."""

    def constraint_decorator(func):
        """Add user constraint to skill."""

        def constraint_callback(message, users=users):
            """Check if the user is correct."""
            return message.user in users

        func = add_skill_attributes(func)
        if invert:
            func.constraints.append(negate(constraint_callback))
        else:
            func.constraints.append(constraint_callback)
        return func

    return constraint_decorator


def constrain_connectors(connectors, invert=False):
    """Return connector constraint decorator."""

    def constraint_decorator(func):
        """Add connectors constraint to skill."""

        def constraint_callback(message, connectors=connectors):
            """Check if the connectors is correct."""
            return message.connector and (message.connector.name in connectors)

        func = add_skill_attributes(func)
        if invert:
            func.constraints.append(negate(constraint_callback))
        else:
            func.constraints.append(constraint_callback)
        return func

    return constraint_decorator
