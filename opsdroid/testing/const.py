"""Constants for use in testing."""

MINIMAL_CONFIG = {
    "connectors": {
        "mock": {"module": "opsdroid.testing.mockmodules.connectors.mocked"}
    },
    "skills": {"hello": {"module": "opsdroid.testing.mockmodules.skills.hello"}},
}
