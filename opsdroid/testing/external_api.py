"""
Testing helpers for opsdroid.

opsdroid provides a set of pytest fixtures and other helpers for writing tests
for both opsdroid core and skills.
"""

import asyncio
from aiohttp import web
import json
from typing import Any, Awaitable, List, Dict

from opsdroid.helper import Timeout


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
                async def test_closure():
                    # Make an HTTP request to our mock_api
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"{mock_api.base_url}/test") as resp:

                            # Assert that it gives the expected responses
                            assert resp.status == 200
                            assert mock_api.called("/test")

                    # Return True to we can ensure the closure was run
                    return True

                # Run the test closure. This will start the web server, and once it is running await
                # the closure. Then when the closure finishes the server will be stopped again and the
                # return from the closure will be passed back.
                assert await mock_api.run_test(test)

    """

    def __init__(self):
        """Initialize a server."""
        self.app = None
        self.runner = None
        self._initialize_web_app()

        self.site = None
        self.host = "localhost"
        self.port = 8089
        self._calls = {}
        self.responses = {}
        self._payloads = {}
        self.status = "stopped"

    def _initialize_web_app(self) -> None:
        self.app = web.Application()
        self.runner = web.AppRunner(self.app)

    async def _start(self) -> None:
        """Start the server."""
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, host=self.host, port=self.port)
        timeout = Timeout(10, "Timed out starting web server")
        while timeout.run():
            try:
                await self.site.start()
                break
            except OSError as e:
                await asyncio.sleep(0.1)
                timeout.set_exception(e)
        self.status = "running"

    async def _stop(self) -> None:
        """Stop the web server."""
        await self.site.stop()
        await self.runner.cleanup()
        self.site = None
        self.status = "stopped"

    async def _handler(self, request: web.Request) -> web.Response:
        route = request.path
        if route in self._calls:
            self._calls[route].append(request)
        else:
            self._calls[route] = [request]
        if route in self._payloads:
            self._payloads[route].append(await request.post())
        else:
            self._payloads[route] = [await request.post()]
        status, response = self.responses[route].pop(0)
        return web.json_response(response, status=status)

    @property
    def base_url(self) -> str:
        """Return the base url of the web server."""
        return f"http://{self.host}:{self.port}"

    def add_response(
        self, route: str, method: str, response_path: str, status: int = 200
    ) -> None:
        """Push a mocked response onto a route."""
        if response_path is not None:
            with open(response_path) as json_file:
                response = json.load(json_file)
        else:
            response = None

        if route in self.responses:
            self.responses[route].append((status, response))
        else:

            if method.upper() == "GET":
                routes = [web.get(route, self._handler)]
            elif method.upper() == "POST":
                routes = [web.post(route, self._handler)]
            else:
                raise TypeError(f"Unsupported method {method}")

            self.responses[route] = [(status, response)]
            self.app.add_routes(routes)

    async def run_test(
        self, test_coroutine: Awaitable, *args: List, **kwargs: Dict
    ) -> Any:
        """Run a test against the web server.

        This method will concurrently start the web server and a test coroutine.
        Once the web server is running the coroutine will be called.

        Args:
            test_coroutine: A coroutine to be called.
            *args: Args to be passed to the coroutine.
            **kwargs: Kwargs to be passed to the coroutine.

        Returns:
            The return from the coroutine.

        """

        async def _run_test_then_stop():
            while self.status != "running":
                await asyncio.sleep(0.1)
            output = await test_coroutine(*args, **kwargs)
            await self._stop()
            return output

        _, run_output = await asyncio.gather(self._start(), _run_test_then_stop())
        return run_output

    def reset(self) -> None:
        """Reset the mock back to a clean state."""
        if self.status == "stopped":
            self._initialize_web_app()
            self._calls = {}
            self.responses = {}
        else:
            raise RuntimeError("Web server must be stopped before it can be reset.")

    def called(self, route: str) -> bool:
        """Route has been called.

        Args:
            route: The API route that we want to know if was called.

        Returns:
            Wether or not it was called.

        """
        return route in self._calls

    def call_count(self, route: str) -> int:
        """Route has been called n times.

        Args:
            route: The API route that we want to know if was called.

        Returns:
            The number of times it was called.

        """
        return len(self._calls[route])

    def get_request(self, route: str, idx: int = 0) -> web.Request:
        """Route has been called n times.

        Args:
            route: The API route that we want to get the request for.
            idx: The index of the call. Useful if it was called multiple times and we want something other than the first one.

        Returns:
            The request that was made.

        """
        return self._calls[route][idx]

    def get_payload(self, route: str, idx: int = 0) -> Dict:
        """Return data payload that the route was called with.

        Args:
            route: The API route that we want to get the payload for.
            idx: The index of the call. Useful if it was called multiple times and we want something other than the first one.

        Returns:
            The data payload which was sent in the POST request.

        """
        return self._payloads[route][idx]
