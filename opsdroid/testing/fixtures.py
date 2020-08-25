"""Core fixtures for testing opsdroid and skills."""
import pytest
import os
import tempfile
import contextlib

from opsdroid.core import OpsDroid

__all__ = ["opsdroid"]


@pytest.fixture
def opsdroid():
    """Fixture with a plain instance of opsdroid.

    Will yield an instance of opsdroid which hasn't been loaded.

    """
    with OpsDroid(config={}) as opsdroid:
        yield opsdroid


@pytest.fixture(scope="module")
def _tmp_dir():
    _tmp_dir = os.path.join(tempfile.gettempdir(), "opsdroid_tests")
    with contextlib.suppress(FileExistsError):
        os.makedirs(_tmp_dir, mode=0o777)
    return _tmp_dir
