# Testing

When making a contribution to opsdroid, it's important that tests are written to validate that the functionality works, and continues to work in the future.

opsdroid is currently slowly migrating from [unittest](https://docs.python.org/3.8/library/unittest.html) to [pytest](https://docs.pytest.org) as it's testing framework.
This work is tracked in issue [#1502](https://github.com/opsdroid/opsdroid/issues/1502).
As a part of this migration tests can be found in one of two places, old unittest tests are found in the `tests/` directory in the root of the repository and new pytest tests are found in a `tests/` directory in the same subfolder as the code, i.e `opsdroid/tests/`.

## Writing new tests with pytest

As well as core pytest, opsdroid is making use of a few different pytest plugins:

-   [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio) for writing and running coroutines as tests. 
    Coroutines should be decorated with `@pytest.mark.asyncio`.
-   [pytest-mock](https://github.com/pytest-dev/pytest-mock/) for proving a convenient interface to mocking parts of the code.
    This package is configured to use the external [mock](https://pypi.org/project/mock/) package, so all versions of Python can use the latest features.

### An example test

Below is an example test, using the pytest-mock, pytest-asyncio and a [fixture](https://docs.pytest.org/en/stable/fixture.html).

```python
from opsdroid.memory import Memory
from opsdroid.database import InMemoryDatabase


@pytest.fixture
def memory():
    mem = Memory()
    mem.databases = [InMemoryDatabase()]
    return mem


@pytest.mark.asyncio
async def test_database_callouts(mocker, memory):
    memory.databases = [mocker.AsyncMock()]
    data = "Hello world!"

    await memory.put("test", data)
    assert memory.databases[0].put.called
```

A pytest fixture sets up an object once per test, making sure that the state is clean for every test that uses it.
It can also perform teardown actions after a `yield` statement.

The `mocker` fixture is provided by pytest-mock, and provides convenient access to things in the mock library, as well as automatic teardown of patches added with `mocker.patch`.

## opsdroid test helpers

```eval_rst
.. automodule:: opsdroid.testing

pytest Fixtures
###############

.. autofunction:: opsdroid.testing.opsdroid
   :noindex:
```
