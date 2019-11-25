"""The start subcommand for opsdroid cli."""


import gettext
import logging
import click

from opsdroid.cli.utils import check_dependencies, configure_lang, welcome_message
from opsdroid.core import OpsDroid
from opsdroid.configuration import load_config_file
from opsdroid.logging import configure_logging
from opsdroid.const import DEFAULT_CONFIG_PATH

gettext.install("opsdroid")
_LOGGER = logging.getLogger("opsdroid")


@click.command()
def start():
    """Start the opsdroid bot."""
    check_dependencies()

    config = load_config_file(
        ["configuration.yaml", DEFAULT_CONFIG_PATH, "/etc/opsdroid/configuration.yaml"]
    )
    configure_lang(config)
    configure_logging(config)
    welcome_message(config)

    with OpsDroid(config=config) as opsdroid:
        opsdroid.run()
