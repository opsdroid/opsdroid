"""Starts opsdroid."""

import os
import subprocess
import sys
import logging
import gettext
import time

import click

from opsdroid import __version__
from opsdroid.core import OpsDroid
from opsdroid.loader import Loader
from opsdroid.logging import configure_logging
from opsdroid.const import (
    DEFAULT_LOG_FILENAME,
    LOCALE_DIR,
    EXAMPLE_CONFIG_FILE,
    DEFAULT_LANGUAGE,
    DEFAULT_CONFIG_PATH,
)


gettext.install("opsdroid")
_LOGGER = logging.getLogger("opsdroid")


def configure_lang(config):
    """Configure app language based on user config.

    Args:
        config: Language Configuration and it uses ISO 639-1 code.
        for more info https://en.m.wikipedia.org/wiki/List_of_ISO_639-1_codes


    """
    lang_code = config.get("lang", DEFAULT_LANGUAGE)
    if lang_code != DEFAULT_LANGUAGE:
        lang = gettext.translation("opsdroid", LOCALE_DIR, (lang_code,), fallback=True)
        lang.install()


def check_dependencies():
    """Check for system dependencies required by opsdroid."""
    if sys.version_info.major < 3 or sys.version_info.minor < 6:
        logging.critical(_("Whoops! opsdroid requires python 3.6 or above."))
        sys.exit(1)


def print_version(ctx, param, value):
    """Print out the version of opsdroid that is installed."""
    if not value or ctx.resilient_parsing:
        return
    click.echo("opsdroid {version}".format(version=__version__))
    ctx.exit(0)


def print_example_config(ctx, param, value):
    """Print out the example config."""
    if not value or ctx.resilient_parsing:
        return
    with open(EXAMPLE_CONFIG_FILE, "r") as conf:
        click.echo(conf.read())
    ctx.exit(0)


def edit_files(ctx, param, value):
    """Open config/log file with favourite editor."""
    if value == "config":
        file = DEFAULT_CONFIG_PATH
    elif value == "log":
        file = DEFAULT_LOG_FILENAME
    else:
        return

    editor = os.environ.get("EDITOR", "vi")
    if editor == "vi":
        click.echo(
            "You are about to edit a file in vim. \n"
            "Read the tutorial on vim at: https://bit.ly/2HRvvrB"
        )
        time.sleep(3)

    subprocess.run([editor, file])
    ctx.exit(0)


def welcome_message(config):
    """Add welcome message if set to true in configuration.

    Args:
        config: config loaded by Loader

    Raises:
        KeyError: If 'welcome-message' key is not found in configuration file

    """
    try:
        if config["welcome-message"]:
            _LOGGER.info("=" * 40)
            _LOGGER.info(
                _(
                    "You can customise your opsdroid by modifying "
                    "your configuration.yaml"
                )
            )
            _LOGGER.info(
                _("Read more at: " "http://opsdroid.readthedocs.io/#configuration")
            )
            _LOGGER.info(_("Watch the Get Started Videos at: " "http://bit.ly/2fnC0Fh"))
            _LOGGER.info(
                _(
                    "Install Opsdroid Desktop at: \n"
                    "https://github.com/opsdroid/opsdroid-desktop/"
                    "releases"
                )
            )
            _LOGGER.info("=" * 40)
    except KeyError:
        _LOGGER.warning(
            _("'welcome-message: true/false' is missing in " "configuration.yaml")
        )


@click.command()
@click.option(
    "--gen-config",
    is_flag=True,
    callback=print_example_config,
    expose_value=False,
    default=False,
    help="Print an example config and exit.",
)
@click.option(
    "--version",
    "-v",
    is_flag=True,
    callback=print_version,
    expose_value=False,
    default=False,
    is_eager=True,
    help="Print the version and exit.",
)
@click.option(
    "--edit-config",
    "-e",
    is_flag=True,
    callback=edit_files,
    default=False,
    flag_value="config",
    expose_value=False,
    help="Opens configuration.yaml with your favorite editor" " and exits.",
)
@click.option(
    "--view-log",
    "-l",
    is_flag=True,
    callback=edit_files,
    default=False,
    flag_value="log",
    expose_value=False,
    help="Opens opsdroid logs with your favorite editor" " and exits.",
)
def main():
    """Opsdroid is a chat bot framework written in Python.

    It is designed to be extendable, scalable and simple.
    See https://opsdroid.github.io/ for more information.
    """
    check_dependencies()

    config = Loader.load_config_file(
        ["configuration.yaml", DEFAULT_CONFIG_PATH, "/etc/opsdroid/configuration.yaml"]
    )
    configure_lang(config)
    configure_logging(config)
    welcome_message(config)

    with OpsDroid(config=config) as opsdroid:
        opsdroid.load()
        opsdroid.run()


def init():
    """Enter the application."""
    if __name__ == "__main__":
        main()


init()
