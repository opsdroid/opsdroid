"""A helper function for parsing event type skills."""

import logging

from opsdroid.events import Event


_LOGGER = logging.getLogger(__name__)


async def parse_event_type(opsdroid, event):
    """Parse an event if it's of a certain type."""
    matched_skills = []
    for skill in opsdroid.skills:
        for matcher in skill.matchers:
            event_type = matcher.get('event_type', {}).get("type", None)
            if event_type:
                # The event type can be specified with a string
                if isinstance(event_type, str):
                    # pylint: disable=invalid-name
                    et = Event.event_registry.get(event_type, None)
                    if et is None:
                        raise ValueError("{event_type} is not a valid opsdroid"
                                         " event representation.".format(
                                             event_type=event_type))
                    event_type = et

                # TODO: Add option to match all subclasses as well
                # if isinstance(event, event_type):
                # pylint: disable=unidiomatic-typecheck
                if type(event) is event_type:
                    matched_skills.append({
                        "score": 1,
                        "skill": skill,
                        "config": skill.config,
                        "message": event
                    })
    return matched_skills
