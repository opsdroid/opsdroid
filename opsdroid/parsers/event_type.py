"""A helper function for parsing event type skills."""

import logging

from opsdroid.events import Event


_LOGGER = logging.getLogger(__name__)


async def parse_event_type(opsdroid, event):
    """Parse an event if it's of a certain type."""
    for skill in opsdroid.skills:
        for matcher in skill.matchers:
            event_type = matcher.get("event_type", {}).get("type", None)
            if event_type:
                # The event type can be specified with a string
                if isinstance(event_type, str):
                    matcher_event_type = Event.event_registry.get(event_type, None)
                    if matcher_event_type is None:
                        raise ValueError(
                            "{event_type} is not a valid opsdroid"
                            " event representation.".format(event_type=event_type)
                        )
                    event_type = matcher_event_type

                # TODO: Add option to match all subclasses as well
                # if isinstance(event, event_type):
                # pylint: disable=unidiomatic-typecheck
                if type(event) is event_type:
                    await opsdroid.run_skill(skill, skill.config, event)
