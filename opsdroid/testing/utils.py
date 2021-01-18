"""Utilities for testing opsdroid."""

import asyncio
import json
import time
from typing import Any, Awaitable, Dict, List
from contextlib import asynccontextmanager

import aiohttp
from aiohttp import web
from opsdroid.core import OpsDroid


@asynccontextmanager
async def running_opsdroid(opsdroid, start_timeout=1):
    """Context manager to control when opsdroid is running.

    This async context manager will start opsdroid running for its duration.
    It can be used like this::

        @pytest.mark.asyncio
        async def test_with_running_opsdroid(opsdroid):
            async with running_opsdroid(opsdroid):
                assert opsdroid.is_running()

    """
    start = time.time()
    asyncio.create_task(opsdroid.start())
    while not opsdroid.is_running() and start + start_timeout > time.time():
        await asyncio.sleep(0.1)
    yield
    await opsdroid.stop()


async def run_unit_test(
    opsdroid: OpsDroid, test: Awaitable, *args: List, start_timeout=1, **kwargs: Dict
) -> Any:
    """Run a unit test function against opsdroid.

    This method should be used when testing on a loaded but stopped instance of opsdroid.
    The instance will be started concurrently with the test runner. The test runner
    will block until opsdroid is ready and then the test will be called. Once the test has returned
    opsdroid will be stopped and unloaded.

    Args:
        opsdroid: A loaded but stopped instance of opsdroid.
        test: A test to execute concurrently with opsdroid once it has been started.
        start_timeout: Wait up to this timeout for opsdroid to say that it is running.

    Returns:
        Passes on the return of the test coroutine.

    Examples:
        An example of running a coroutine test against opsdroid::

            import pytest
            from opsdroid.testing import (
                opsdroid,
                run_unit_test,
                MINIMAL_CONFIG
                )

            @pytest.mark.asyncio
            async def test_example(opsdroid):
                # Using the opsdrid fixture we load it with the
                # minimal example config
                await opsdroid.load(config=MINIMAL_CONFIG)

                # Check that opsdroid is not currently running
                assert not opsdroid.is_running()

                # Define an awaitable closure which asserts that
                # opsdroid is now running
                async def test():
                    assert opsdroid.is_running()
                    return True  # So that we can assert our run test

                # Run our closure against opsdroid. This will start opsdroid,
                # await our closure and then stop opsdroid again.
                assert await run_unit_test(opsdroid, test)

    """

    async def runner():
        start = time.time()
        while not opsdroid.is_running() and start + start_timeout > time.time():
            await asyncio.sleep(0.1)
        result = await test(*args, **kwargs)
        await opsdroid.stop()
        return result

    _, output = await asyncio.gather(opsdroid.start(), runner())
    return output


async def call_endpoint(
    opsdroid: OpsDroid,
    endpoint: str,
    method: str = "GET",
    data_path: str = None,
    data: Dict = None,
) -> web.Response:
    """Call an opsdroid API endpoint with the provided data.

    This method should be used when testing on a running instance of opsdroid.
    The endpoint will be appended to the base url of the running opsdroid, so you do not
    need to know the address of the running opsdroid. An HTTP request will be made with
    the provided method and data or data_path for methods that support it.

    For methods like ``"POST"`` either ``data`` or ``data_path`` should be set.

    Args:
        opsdroid: A running instance of opsdroid.
        endpoint: The API route to call.
        method: The HTTP method to use when calling.
        data_path: A local file path to load a JSON payload from to be sent in supported methods.
        data: A dictionary payload to be sent in supported methods.

    Returns:
        The response from the HTTP request.

    Examples:
        Call the ``/stats`` endpoint of opsdroid without having to know what address opsdroid
        is serving at::

            import pytest
            from opsdroid.testing import (
                opsdroid,
                call_endpoint,
                run_unit_test,
                MINIMAL_CONFIG
                )

            @pytest.mark.asyncio
            async def test_example(opsdroid):
                # Using the opsdrid fixture we load it with the
                # minimal example config
                await opsdroid.load(config=MINIMAL_CONFIG)

                async def test():
                    # Call our endpoint by just passing
                    # opsdroid, the endpoint and the method
                    resp = await call_endpoint(opsdroid, "/stats", "GET")

                    # Make assertions that opsdroid responded successfully
                    assert resp.status == 200
                    return True

                assert await run_unit_test(opsdroid, test)

    """
    if data_path:
        with open(data_path) as json_file:
            data = json.load(json_file)

    # 0.0.0.0 is problematic (at least) on windows
    base_url = opsdroid.web_server.base_url.replace("//0.0.0.0:", "//127.0.0.1:")

    async with aiohttp.ClientSession() as session:
        if method.upper() == "GET":
            async with session.get(f"{base_url}{endpoint}") as resp:
                return resp
        elif method.upper() == "POST":
            if data_path is None and data is None:
                raise RuntimeError("Either data or data_path must be set")
            async with session.post(f"{base_url}{endpoint}", data=data) as resp:
                return resp
        else:
            raise TypeError(f"Unsupported method {method}")
