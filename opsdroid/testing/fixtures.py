"""Core fixtures for testing opsdroid and skills.

These are not in conftest.py so that they can be imported in sub-projects.
"""
import contextlib
import socket
from typing import Tuple

import pytest

from opsdroid.core import OpsDroid
from opsdroid.connector import Connector

from .external_api import ExternalAPIMockServer

__all__ = ["mock_api_obj", "bound_address", "get_connector", "opsdroid", "mock_api"]


@pytest.fixture(scope="session")
def get_connector():
    """Pytest fixture which is a factory to generate a connector."""

    def _get_connector(config={}, opsdroid=None):
        return Connector(config, opsdroid=opsdroid)

    return _get_connector


@pytest.fixture
def bound_address(request) -> Tuple[str, int]:
    """Block an unused port and return it.

    This allows testing ``except OSError`` blocks that check for a port-in-use.

    For example, this test ensures that OSError is propagated
    when the port is already in use on localhost:

        async def test_web_port_in_use(opsdroid, bound_address):
            opsdroid.config["web"] = {
                "host": bound_address[0], "port": bound_address[1]
            }
            app = web.Web(opsdroid)
            with pytest.raises(OSError):
                await app.start()

    By default this blocks a port with host 0.0.0.0, but you can use parametrize
    to specify an alternate host:

        @pytest.mark.parametrize("bound_address", ["localhost"], indirect=True)
        async def test_localhost(bound_address):
            assert bound_address[0] == "localhost"
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    with contextlib.suppress(socket.error):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):  # only on windows
            s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        if hasattr(socket, "SO_REUSEPORT"):  # not on windows
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 0)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)

    host = request.param if hasattr(request, "param") else "0.0.0.0"
    s.bind((host, 0))  # an ephemeral port
    yield s.getsockname()
    s.close()


@pytest.fixture
def opsdroid() -> OpsDroid:
    """Fixture with a plain instance of opsdroid.

    Will yield an instance of :class:`opsdroid.core.OpsDroid` which hasn't been loaded.

    """
    with OpsDroid(config={}) as opsdroid:
        yield opsdroid


@pytest.fixture
def mock_api_obj(request) -> ExternalAPIMockServer:
    """Initialize instance of :class:`opsdroid.testing.ExternalAPIMockServer`.

    This fixture returns an instance that hasn't been started, allowing you to
    add routes to the server before it is started.
    There are a few options of how to start the server once this fixture has
    been used:

        * Use the ``mock_api`` fixture in the test *after* this fixture has
          been called to setup a route.
        * Use the
          :meth:`opsdroid.testing.ExternalAPIMockServer.running`
          context manager.
        * Manually start and stop the server.

    An example of the second method is to define a fixture which adds a
    response, and then use the ``mock_api`` fixture in the test to start the
    server::

        @pytest.fixture
        def canned_response(mock_api_obj):
            mock_api_obj.add_response("/test", "GET")

        # Note here mock_api MUST come after canned_response for the route to
        # be added before the server is started.
        def test_my_endpoint(canned_response, mock_api):
            ...

    Routes can be specified with ``pytest.mark.add_response`` on tests using
    this fixture, as described in :func:`~opsdroid.testing.fixtures.mock_api`
    """
    mock_api_obj = ExternalAPIMockServer()
    markers = [
        marker for marker in request.node.own_markers if marker.name == "add_response"
    ]

    for marker in markers:
        mock_api_obj.add_response(*marker.args, **marker.kwargs)

    return mock_api_obj


@pytest.fixture
async def mock_api(mock_api_obj) -> ExternalAPIMockServer:
    """Fixture for mocking API calls to a web service.

    Will yield a running instance of
    :class:`opsdroid.testing.ExternalAPIMockServer`, which has been configured
    with any routes specified through ``@pytest.mark.add_response()``
    decorators, or modification of the
    :func:`~opsdroid.testing.fixtures.mock_api_obj` fixture before the test is
    called.

    All arguments and keyword arguments passed to ``pytest.mark.add_response``
    are passed through to `.ExternalAPIMockServer.add_response`.

    An example test would look like::

        @pytest.mark.add_response("/test", "GET")
        @pytest.mark.add_response("/test2", "GET", status=500)
        @pytest.mark.asyncio
        async def test_hello(mock_api):
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{mock_api.base_url}/test") as resp:
                    assert resp.status == 200
                    assert mock_api.called("/test")

                async with session.get(f"{mock_api.base_url}/test2") as resp:
                    assert resp.status == 500
                    assert mock_api.called("/test2")

    """
    async with mock_api_obj.running() as mock_api:
        yield mock_api
