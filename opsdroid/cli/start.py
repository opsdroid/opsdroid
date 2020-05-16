"""The start subcommand for opsdroid cli."""


import gettext
import logging
import click

from opsdroid.cli.utils import (
    check_dependencies,
    configure_lang,
    welcome_message,
    path_option,
)
from opsdroid.core import OpsDroid
from opsdroid.configuration import load_config_file
from opsdroid.logging import configure_logging
from opsdroid.const import DEFAULT_CONFIG_LOCATIONS

gettext.install("opsdroid")
_LOGGER = logging.getLogger("opsdroid")


@click.command()
@path_option
def start(path):
    """Start the opsdroid bot.

    If the `-f` flag is used with this command, opsdroid will load the
    configuration specified on that path otherwise it will use the default
    configuration.

    """
    check_dependencies()

    config_path = [path] if path else DEFAULT_CONFIG_LOCATIONS
    config = load_config_file(config_path)

    configure_lang(config)
    configure_logging(config)
    welcome_message(config)

    with OpsDroid(config=config, config_path=config_path) as opsdroid:
        opsdroid.run()
