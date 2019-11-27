"""The start subcommand for opsdroid cli."""


import gettext
import logging
import click

from opsdroid.cli.utils import check_dependencies, configure_lang, welcome_message
from opsdroid.core import OpsDroid
from opsdroid.configuration import load_config_file
from opsdroid.logging import configure_logging
from opsdroid.const import DEFAULT_CONFIG_LOCATIONS

gettext.install("opsdroid")
_LOGGER = logging.getLogger("opsdroid")


@click.command()
@click.option(
    "-f",
    "path",
    help="Load opsdroid configuration from a path.",
    type=click.Path(exists=True),
)
def start(path):
    """Start the opsdroid bot."""
    check_dependencies()

    config = load_config_file([path] if path else DEFAULT_CONFIG_LOCATIONS)

    configure_lang(config)
    configure_logging(config)
    welcome_message(config)

    with OpsDroid(config=config) as opsdroid:
        opsdroid.run()
