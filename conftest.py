import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--only-signal-tests",
        action="store_true",
        default=False,
        help=(
            "run tests that test OpsDroid signal handling. "
            "When --only-signal-tests is not specified, signal tests are skipped. "
            "When --only-signal-tests is specified, all other tests are skipped."
        ),
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "isolate_signal_test: mark test as a signal test that requires isolation",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--only-signal-tests"):
        # don't report all other tests as skipped, just ignore them
        items[:] = [item for item in items if "isolate_signal_test" in item.keywords]
    else:
        skip_signal_tests = pytest.mark.skip(
            reason="need --only-signal-tests option to run"
        )
        for item in items:
            if "isolate_signal_test" in item.keywords:
                item.add_marker(skip_signal_tests)
