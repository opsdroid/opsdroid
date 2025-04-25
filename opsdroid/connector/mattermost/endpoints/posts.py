import logging
from .base import Base

_LOGGER = logging.getLogger(__name__)


class Posts(Base):
    endpoint = "/posts"

    def create_post(self, json):
        _LOGGER.debug("Sending post with payload '%s'", repr(json))
        return self.post(self.endpoint, json=json)

    def get_post(self, post_id):
        _LOGGER.debug("Getting post with id '%s'", repr(post_id))
        return self.get(f"{self.endpoint}/{post_id}")
