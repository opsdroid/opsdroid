import logging
from .base import Base
from .teams import Teams

_LOGGER = logging.getLogger(__name__)


class Channels(Base):
    endpoint = "/channels"

    def get_channel_for_team_by_name(self, team_name, channel_name):
        _LOGGER.debug(
            "Querying channel for team '%s' and name '%s'", team_name, channel_name
        )

        return self.get(
            f"{Teams.endpoint}/name/{team_name}/channels/name/{channel_name}"
        )

    def get_channel_by_id(self, channel_id):
        _LOGGER.debug("Querying channel for ID '%s'", channel_id)

        return self.get(f"{self.endpoint}/{channel_id}")
