import logging
from .base import Base

_LOGGER = logging.getLogger(__name__)


class Posts(Base):
    endpoint = "/posts"

    def create_post(self, json):
        _LOGGER.debug("Sending post with payload '%s'", repr(json))
        return self.post(self.endpoint, json=json)
