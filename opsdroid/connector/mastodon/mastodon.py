import asyncio

from mastodon import Mastodon

from opsdroid.connector import Connector, register_event
from opsdroid.events import Message

CONFIG_SCHEMA = {"access-token": str, "api-base-url": str}


class ConnectorMastodon(Connector):
    def __init__(self, config, opsdroid):
        self.name = "mastodon"
        self.config = config
        self.default_target = None
        self.opsdroid = opsdroid
        self.mastodon = None

    async def connect(self):
        self.mastodon = Mastodon(
            access_token=self.config.get("access-token"),
            api_base_url=self.config.get("api-base-url"),
        )

    async def listen(self):
        pass

    @register_event(Message)
    async def send(self, message):
        await asyncio.get_event_loop().run_in_executor(
            None, self.mastodon.status_post, message.text
        )
