import asyncio
import tempfile

from mastodon import Mastodon

from opsdroid.connector import Connector, register_event
from opsdroid.events import Message, Image, Event

CONFIG_SCHEMA = {"access-token": str, "api-base-url": str}


class Toot(Event):
    def __init__(self, text, images=None):
        self.text = text
        self.target = None
        if images and len(images) > 4:
            raise ValueError("Mastodon only supports 4 images per toot.")
        self.images = images


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

    async def upload_image(self, image):
        with tempfile.NamedTemporaryFile() as tmpfh:
            tmpfh.write(await image.get_file_bytes())
            media = await asyncio.get_event_loop().run_in_executor(
                None, self.mastodon.media_post, tmpfh.name, await image.get_mimetype()
            )
        return media

    @register_event(Image)
    async def send_image(self, image):
        media = await self.upload_image(image)
        await asyncio.get_event_loop().run_in_executor(
            None, lambda: self.mastodon.status_post("", media_ids=[media["id"]])
        )

    @register_event(Toot)
    async def send_toot(self, toot):
        media_ids = [
            (await self.upload_image(image))["id"] for image in toot.images
        ] or None
        await asyncio.get_event_loop().run_in_executor(
            None, lambda: self.mastodon.status_post(toot.text, media_ids=media_ids)
        )

    @register_event(Message)
    async def send_message(self, message):
        await asyncio.get_event_loop().run_in_executor(
            None, lambda: self.mastodon.status_post(message.text)
        )
