import pytest

from opsdroid.core import OpsDroid


@pytest.fixture
def opsdroid():
    with OpsDroid() as opsdroid:
        yield opsdroid
