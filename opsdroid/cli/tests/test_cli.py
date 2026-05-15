import os
import unittest.mock as mock

import click
from click.testing import CliRunner
import pytest

import opsdroid.__main__
import opsdroid.cli
import opsdroid.cli.version
from opsdroid.cli.start import configure_lang
from opsdroid.cli.utils import configure_lang as configure_lang_utils
from opsdroid.cli.utils import welcome_message
from opsdroid.cli.config import gen, edit, build, lint, list_modules
from opsdroid.cli import config as config_group
from opsdroid.cli.version import version
from opsdroid.cli.logs import logs
from opsdroid.const import __version__
from opsdroid.core import OpsDroid


pytestmark = pytest.mark.usefixtures("configure_lang_fixture")


@pytest.fixture(autouse=True)
def configure_lang_fixture():
    """Configure language for CLI tests."""
    configure_lang({})


def test_init_runs():
    """Test that init() calls cli() when run as __main__."""
    with mock.patch.object(opsdroid.cli, "cli") as mainfunc:
        with mock.patch.object(opsdroid.__main__, "__name__", "__main__"):
            opsdroid.__main__.init()
            assert mainfunc.called


def test_init_doesnt_run():
    """Test that init() does not call cli() when imported."""
    with mock.patch.object(opsdroid.cli, "cli") as mainfunc:
        with mock.patch.object(opsdroid.__main__, "__name__", "opsdroid"):
            opsdroid.__main__.init()
            assert not mainfunc.called


def test_configure_no_lang():
    """Test configure_lang() with no language config."""
    with mock.patch("opsdroid.cli.start.gettext.translation") as translation:
        configure_lang({})
        assert not translation.return_value.install.called


def test_configure_lang():
    """Test configure_lang() with Spanish language config."""
    with mock.patch("opsdroid.cli.utils.gettext.translation") as translation:
        configure_lang_utils({"lang": "es"})
        assert translation.return_value.install.called


def test_welcome_message():
    """Test that welcome_message() logs an info message."""
    config = {"welcome-message": True}
    welcome_message(config)


def test_welcome_exception():
    """Test that welcome_message() handles missing config gracefully."""
    config = {}
    response = welcome_message(config)
    assert response is None


def test_gen_config():
    """Test that the config generate command does not load opsdroid."""
    with mock.patch.object(click, "echo") as click_echo, mock.patch(
        "opsdroid.core.OpsDroid.load"
    ) as opsdroid_load:
        runner = CliRunner()
        result = runner.invoke(gen, [])
        assert click_echo.called
        assert not opsdroid_load.called
        assert result.exit_code == 0


def test_print_version():
    """Test that the version command prints the version."""
    with mock.patch.object(click, "echo") as click_echo, mock.patch(
        "opsdroid.core.OpsDroid.load"
    ) as opsdroid_load:
        runner = CliRunner()
        result = runner.invoke(version, [])
        assert click_echo.called
        assert not opsdroid_load.called
        assert __version__ in click_echo.call_args[0][0]
        assert result.exit_code == 0


def test_edit_files_config():
    """Test that the config edit command opens an editor."""
    with mock.patch.object(click, "echo"), mock.patch("subprocess.run") as editor:
        runner = CliRunner()
        result = runner.invoke(edit, [], input="y")
        assert editor.called
        assert result.exit_code == 0


def test_print_files_log():
    """Test that the logs command prints log files."""
    with mock.patch.object(click, "echo") as click_echo:
        runner = CliRunner()
        result = runner.invoke(logs, [])
        assert click_echo.called
        assert result.exit_code == 0


def test_print_files_log_follow():
    """Test that the logs -f command follows log output."""
    with mock.patch.object(click, "echo") as click_echo, mock.patch(
        "tailer.follow"
    ) as tailer_follow, mock.patch("builtins.open"):
        runner = CliRunner()
        tailer_follow.return_value = ["line 1", "line 2"]
        runner.invoke(logs, ["-f"])
        assert tailer_follow.called
        assert click_echo.called


def test_main():
    """Test that the main start command runs opsdroid."""
    runner = CliRunner()
    with mock.patch.object(OpsDroid, "run") as mock_run:
        runner.invoke(opsdroid.cli.start, [])
        assert mock_run.called


def test_config_validate():
    """Test that the config lint command validates config without loading opsdroid."""
    with mock.patch.object(click, "echo") as click_echo, mock.patch(
        "opsdroid.configuration.load_config_file"
    ) as opsdroid_load:
        runner = CliRunner()
        result = runner.invoke(lint, [])
        assert click_echo.called
        assert not opsdroid_load.called
        assert result.exit_code == 0


def test_config_list_modules():
    """Test that the config list-modules command lists available modules."""
    with mock.patch.object(click, "echo") as click_echo:
        runner = CliRunner()
        result = runner.invoke(list_modules, [])
        assert click_echo.called
        assert result.exit_code == 0


def test_start_from_path():
    """Test that opsdroid can start with a config file path."""
    runner = CliRunner()
    with mock.patch.object(OpsDroid, "run") as mock_run:
        runner.invoke(
            opsdroid.cli.start,
            ["-f", os.path.abspath("tests/configs/full_valid.yaml")],
        )
        assert mock_run.called


def test_config_validate_from_path():
    """Test that config lint works with a custom config path."""
    with mock.patch.object(click, "echo") as click_echo, mock.patch(
        "opsdroid.configuration.load_config_file"
    ) as opsdroid_load:
        runner = CliRunner()
        result = runner.invoke(
            config_group, ["-f", os.path.abspath("tests/configs/full_valid.yaml"), "lint"]
        )
        assert click_echo.called
        assert not opsdroid_load.called
        assert result.exit_code == 0


def test_config_build_from_path():
    """Test that config build works with a custom config path."""
    with mock.patch.object(click, "echo") as click_echo, mock.patch(
        "opsdroid.configuration.load_config_file"
    ) as opsdroid_load:
        runner = CliRunner()
        result = runner.invoke(
            config_group,
            [
                "-f",
                os.path.abspath("tests/configs/full_valid.yaml"),
                "build",
                "--verbose",
            ],
        )
        assert click_echo.called
        assert not opsdroid_load.called
        assert result.exit_code == 0


def test_config_build():
    """Test that the config build command works."""
    with mock.patch.object(click, "echo") as click_echo, mock.patch(
        "opsdroid.configuration.load_config_file"
    ) as opsdroid_load:
        runner = CliRunner()
        result = runner.invoke(build, [])
        assert click_echo.called
        assert not opsdroid_load.called
        assert result.exit_code == 0


def test_config_build_exception():
    """Test that config build handles exceptions gracefully."""
    with mock.patch.object(click, "echo") as click_echo, mock.patch(
        "opsdroid.configuration.load_config_file"
    ), mock.patch("opsdroid.loader") as mock_load:
        mock_load.load_modules_from_config.side_effect = Exception()
        runner = CliRunner()
        result = runner.invoke(build, [])
        assert click_echo.called
        assert result.exit_code == 0
