"""Pytest config for all opsdroid tests."""
import pytest

import asyncio
from aiohttp import web
import json

from opsdroid.core import OpsDroid


@pytest.fixture
def opsdroid():
    """Fixture with a plain instance of opsdroid.

    Will yield an instance of opsdroid which hasn't been loaded.

    """
    with OpsDroid(config={}) as opsdroid:
        yield opsdroid


class ExternalAPIMockServer:
    """A webserver which can pretend to be an external API."""

    def __init__(self):
        """Setup a server."""
        self.app = web.Application()
        self.runner = web.AppRunner(self.app)
        self.site = None
        self.host = "localhost"
        self.port = 8089
        self.calls = {}
        self.responses = {}
        self.status = "stopped"

    async def _start(self):
        """Start the server."""
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, host=self.host, port=self.port)
        await self.site.start()
        self.status = "running"

    async def _stop(self):
        """Stop the web server."""
        await self.runner.cleanup()
        self.status = "stopped"

    async def _handler(self, request):
        route = request.path
        if route in self.calls:
            self.calls[route].append(request)
        else:
            self.calls[route] = [request]
        status, response = self.responses[route].pop(0)
        return web.json_response(response, status=status)

    @property
    def base_url(self):
        return f"http://{self.host}:{self.port}"

    def add_response(self, route, method, response_path, status=200):
        """Push a mocked response onto a route."""
        if response_path is not None:
            with open(response_path) as json_file:
                response = json.load(json_file)
        else:
            response = None

        if route in self.responses:
            self.responses[route].append((status, response))
        else:
            self.responses[route] = [(status, response)]

        if method.upper() == "GET":
            routes = [web.get(route, self._handler)]
        elif method.upper() == "POST":
            routes = [web.post(route, self._handler)]
        else:
            raise TypeError(f"Unsupported method {method}")

        self.app.add_routes(routes)

    async def run_test(self, test_coroutine):
        async def _run():
            while self.status != "running":
                await asyncio.sleep(0.1)
            await test_coroutine()
            await self._stop()

        await asyncio.gather(_run(), self._start())

    def called(self, route):
        return route in self.calls

    def call_count(self, route):
        return len(self.calls[route])

    def get_request(self, route, idx=0):
        return self.calls[route][idx]


@pytest.fixture
async def mock_api():
    return ExternalAPIMockServer()
