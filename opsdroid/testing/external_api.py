"""
Testing helpers for opsdroid.

opsdroid provides a set of pytest fixtures and other helpers for writing tests
for both opsdroid core and skills.
"""
import asyncio
from collections import defaultdict
import json
from contextlib import asynccontextmanager
from os import PathLike
from typing import Any, Dict, Union

from aiohttp import web
from opsdroid.helper import Timeout
from multidict import (
    MultiDict,
    MultiDictProxy,
)


class ExternalAPIMockServer:
    """A webserver which can pretend to be an external API.

    The general idea with this class is to allow you to push expected responses onto
    a stack for each API call you expect your test to make. Then as your tests make those
    calls each response is popped from the stack.

    You can then assert that routes were called and that data and headers were sent correctly.

    Your test will need to switch the URL of the API calls, so the thing you are testing should be
    configurable at runtime. You will also need to capture the responses from the real API your are
    mocking and store them as JSON files. Then you can push those responses onto the stack at the start
    of your test.

    Examples:
        A simple example of pushing a response onto a stack and making a request::

            import pytest
            import aiohttp

            from opsdroid.testing import ExternalAPIMockServer

            @pytest.mark.asyncio
            async def test_example():
                # Construct the mock API server and push on a test method
                mock_api = ExternalAPIMockServer()
                mock_api.add_response("/test", "GET", None, 200)

                # Create a closure function. We will have our mock_api run this concurrently with the
                # web server later.
                async with mock_api.running():
                    # Make an HTTP request to our mock_api
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"{mock_api.base_url}/test") as resp:

                            # Assert that it gives the expected responses
                            assert resp.status == 200
                            assert mock_api.called("/test")

    """

    def __init__(self):
        """Initialize a server."""
        self.app = None
        self.runner = None
        self._initialize_web_app()

        self.site = None
        self.host = "localhost"
        self.port = 8089
        self._calls = defaultdict(list)
        self.responses = defaultdict(list)
        self._payloads = defaultdict(list)
        self.status = "stopped"
        self.start_timeout = 10  # seconds

    def _initialize_web_app(self) -> None:
        self.app = web.Application()
        self.runner = web.AppRunner(self.app)

    async def start(self) -> None:
        """Start the server."""
        await self.runner.setup()
        timeout = Timeout(self.start_timeout, "Timed out starting web server")
        while timeout.run():
            try:
                self.site = web.TCPSite(self.runner, host=self.host, port=self.port)
                await self.site.start()
                break
            except OSError as e:
                await asyncio.sleep(0.1)
                timeout.set_exception(e)
                await self.site.stop()
        self.status = "running"

    async def stop(self) -> None:
        """Stop the web server."""
        await self.site.stop()
        await self.runner.cleanup()
        self.site = None
        self.status = "stopped"

    async def _handler(self, request: web.Request) -> web.Response:
        route = request.path
        method = request.method

        self._calls[(route, method)].append(request)

        post_data = await request.post()  # try and parse form data first

        if post_data == MultiDictProxy(MultiDict()):
            if request.can_read_body:  # if it's not form data, try and parse as json
                self._payloads[route].append(await request.json())
            else:
                self._payloads[route].append(post_data)
        else:
            self._payloads[route].append(post_data)

        status, response = self.responses[(route, method)].pop(0)
        if isinstance(response, str):
            return web.Response(text=response, status=status, content_type="text/html")
        return web.json_response(response, status=status)

    async def _websockethandler(self, request: web.Request) -> web.WebSocketResponse:
        route = request.path
        method = "WEBSOCKET"
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        self._calls[(route, method)].append(request)
        post_data = await request.post()  # try and parse form data first

        if post_data == MultiDictProxy(MultiDict()):
            if request.can_read_body:  # if it's not form data, try and parse as json
                self._payloads[route].append(await request.json())
            else:
                self._payloads[route].append(post_data)
        else:
            self._payloads[route].append(post_data)

        while len(self.responses[(route, method)]) > 0:
            _, response = self.responses[(route, method)].pop(0)
            if isinstance(response, str):
                await ws.send_str(response)
            else:
                await ws.send_json(response)
        return ws

    @property
    def base_url(self) -> str:
        """Return the base url of the web server."""
        return f"http://{self.host}:{self.port}"

    def add_response(
        self,
        route: str,
        method: str,
        response: Union[Any, PathLike] = None,
        status: int = 200,
    ) -> None:
        """Push a mocked response onto a route."""
        if isinstance(response, PathLike):
            with open(response) as json_file:
                response = json.load(json_file)
        else:
            response = response

        if (route, method) not in self.responses:
            if method.upper() == "GET":
                routes = [web.get(route, self._handler)]
            elif method.upper() == "POST":
                routes = [web.post(route, self._handler)]
            elif method.upper() == "PUT":
                routes = [web.put(route, self._handler)]
            elif method.upper() == "WEBSOCKET":
                routes = [web.get(route, self._websockethandler)]
            else:
                raise TypeError(f"Unsupported method {method}")
            self.app.add_routes(routes)

        self.responses[(route, method)].append((status, response))

    @asynccontextmanager
    async def running(self) -> "ExternalAPIMockServer":
        """Start the External API server within a context manager."""
        await self.start()
        yield self
        await self.stop()

    def reset(self) -> None:
        """Reset the mock back to a clean state."""
        if self.status == "stopped":
            self._initialize_web_app()
            self._calls = {}
            self.responses = {}
        else:
            raise RuntimeError("Web server must be stopped before it can be reset.")

    def called(self, route: str, method: str = None) -> bool:
        """Route has been called.

        Args:
            route: The API route that we want to know if was called.

        Returns:
            Wether or not it was called.

        """
        if not method:
            return route in [k[0] for k in self._calls.keys()]

        return (route, method) in self._calls

    def call_count(self, route: str, method: str = None) -> int:
        """Route has been called n times.

        Args:
            route: The API route that we want to know if was called.

        Returns:
            The number of times it was called.

        """
        if not method:
            all_calls = [
                len(call[1]) for call in self._calls.items() if call[0][0] == route
            ]
            return sum(all_calls)

        return len(self._calls[(route, method)])

    def get_request(self, route: str, method: str, idx: int = 0) -> web.Request:
        """Route has been called n times.

        Args:
            route: The API route that we want to get the request for.
            idx: The index of the call. Useful if it was called multiple times and we want something other than the first one.

        Returns:
            The request that was made.

        """
        return self._calls[(route, method)][idx]

    def get_payload(self, route: str, idx: int = 0) -> Dict:
        """Return data payload that the route was called with.

        Args:
            route: The API route that we want to get the payload for.
            idx: The index of the call. Useful if it was called multiple times and we want something other than the first one.

        Returns:
            The data payload which was sent in the POST request.

        """
        return self._payloads[route][idx]
