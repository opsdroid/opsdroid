from aiohttp.client import ClientSession, ClientResponse
from asyncio import Task


class Base:
    def __init__(self, client: ClientSession, base_url: str):
        self._internal_client = client
        self._base_url = base_url

    def create_future(self, func) -> Task[ClientResponse]:
        """
        Wraps a function to be called in the event loop.

        :param func: Function to be called
        :return: Future object
        """
        return self._internal_client.loop.create_task(func)

    def get(self, path, **kwargs):
        return self._internal_client.get(
            "{base_url}{path}".format(base_url=self._base_url, path=path), **kwargs
        )

    def post(self, path, **kwargs):
        return self._internal_client.post(
            "{base_url}{path}".format(base_url=self._base_url, path=path), **kwargs
        )
