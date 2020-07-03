# Testing

Opsdroid contains tooling for testing which is useful for testing opsdroid itself but also for testing your skills and any `Connectors`, `Parsers` and `Databases` created outside the core project.

Opsdroid tests are run using `pytest`. Fixtures can be imported into your own projects, and are available by default in opsdroid core tests.

There are also some utilities for mocking our and running tests specific to opsdroid.

## Fixtures

```eval_rst
.. autofunction:: opsdroid.testing.opsdroid
```

```eval_rst
.. autofunction:: opsdroid.testing.mock_api
```

## Utilities

```eval_rst
.. autoclass:: opsdroid.testing.ExternalAPIMockServer
   :members:
```

```eval_rst
.. autofunction:: opsdroid.testing.run_unit_test
```

```eval_rst
.. autofunction:: opsdroid.testing.call_endpoint
```
