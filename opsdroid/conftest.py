"""Pytest config for all opsdroid tests."""
import pytest

from opsdroid.core import OpsDroid


@pytest.fixture
def opsdroid():
    """Fixture with a plain instance of opsdroid.

    Will yield an instance of opsdroid which hasn't been loaded.

    """
    with OpsDroid(config={}) as opsdroid:
        yield opsdroid
