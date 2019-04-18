"""Decorator functions to use when creating skill modules.

These decorators are for specifying when a skill should not be called despite
having a matcher which matches the current message.
"""

import logging

from opsdroid.helper import add_skill_attributes


_LOGGER = logging.getLogger(__name__)


def constrain_rooms(rooms):
    """Return room constraint decorator."""
    def constraint_decorator(func):
        """Add room constraint to skill."""
        def constraint_callback(message, rooms=rooms):
            """Check if the room is correct."""
            return message.target in rooms
        func = add_skill_attributes(func)
        func.constraints.append(constraint_callback)
        return func
    return constraint_decorator


def constrain_users(users):
    """Return user constraint decorator."""
    def constraint_decorator(func):
        """Add user constraint to skill."""
        def constraint_callback(message, users=users):
            """Check if the user is correct."""
            return message.user in users
        func = add_skill_attributes(func)
        func.constraints.append(constraint_callback)
        return func
    return constraint_decorator


def constrain_connectors(connectors):
    """Return connector constraint decorator."""
    def constraint_decorator(func):
        """Add connectors constraint to skill."""
        def constraint_callback(message, connectors=connectors):
            """Check if the connectors is correct."""
            print(message.connector.name)
            print(connectors)
            return message.connector.name in connectors
        func = add_skill_attributes(func)
        func.constraints.append(constraint_callback)
        return func
    return constraint_decorator
