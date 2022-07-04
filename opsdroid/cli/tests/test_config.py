from click.testing import CliRunner

from opsdroid.cli.config import path
from opsdroid.const import DEFAULT_CONFIG_PATH


def test_config_path():
    runner = CliRunner()
    result = runner.invoke(path)
    assert result.exit_code == 0
    assert DEFAULT_CONFIG_PATH in result.output
