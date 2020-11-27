"""Core fixtures for testing opsdroid and skills."""
import pytest

from opsdroid.core import OpsDroid
from .external_api import ExternalAPIMockServer

__all__ = ["opsdroid", "mock_api"]


@pytest.fixture
def opsdroid() -> OpsDroid:
    """Fixture with a plain instance of opsdroid.

    Will yield an instance of :class:`opsdroid.core.OpsDroid` which hasn't been loaded.

    """
    with OpsDroid(config={}) as opsdroid:
        yield opsdroid


@pytest.fixture
async def mock_api() -> ExternalAPIMockServer:
    """Fixture for making a mock API server.

    Will give an instance of :class:`opsdroid.testing.ExternalAPIMockServer`.

    """
    return ExternalAPIMockServer()
