"""Utilities for the opsdroid CLI commands."""

import click
import gettext
import os
import logging
import subprocess
import sys
import time
import warnings

from opsdroid.core import OpsDroid
from opsdroid.loader import Loader
from opsdroid.configuration import load_config_file
from opsdroid.const import (
    DEFAULT_LOG_FILENAME,
    LOCALE_DIR,
    DEFAULT_LANGUAGE,
    DEFAULT_CONFIG_PATH,
)

_LOGGER = logging.getLogger("opsdroid")


def edit_files(ctx, param, value):
    """Open config/log file with favourite editor.

    Args:
        ctx (:obj:`click.Context`): The current click cli context.
        param (dict): a dictionary of all parameters pass to the click
            context when invoking this function as a callback.
        value (string): the value of this parameter after invocation.
            It is either "config" or "log" depending on the program
            calling this function.

    Returns:
        int: the exit code. Always returns 0 in this case.

    """

    if value == "config":
        file = DEFAULT_CONFIG_PATH
        if ctx.command.name == "cli":
            warn_deprecated_cli_option(
                "The flag -e/--edit-files has been deprecated. "
                "Please run `opsdroid config edit` instead."
            )
    elif value == "log":
        file = DEFAULT_LOG_FILENAME
        if ctx.command.name == "cli":
            warn_deprecated_cli_option(
                "The flag -l/--view-log has been deprecated. "
                "Please run `opsdroid logs` instead."
            )
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


def validate_config(ctx, param, value):
    """Open config/log file with favourite editor.

    Args:
        ctx (:obj:`click.Context`): The current click cli context.
        param (dict): a dictionary of all parameters pass to the click
            context when invoking this function as a callback.
        value (string): the value of this parameter after invocation.
            It is either "config" or "log" depending on the program
            calling this function.

    Returns:
        int: the exit code. Always returns 0 in this case.

    """
    loader = Loader(OpsDroid)
    config = load_config_file(
        ["configuration.yaml", DEFAULT_CONFIG_PATH, "/etc/opsdroid/configuration.yaml"]
    )
    loader.load_modules_from_config(config)
    if config:
        click.echo("Configuration validated - No errors founds!")

    ctx.exit(0)


def warn_deprecated_cli_option(text):
    """Warn users that the cli option they have used is deprecated."""
    print(f"Warning: {text}")
    warnings.warn(text, DeprecationWarning)


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
    """Check for system dependencies required by opsdroid.

    Returns:
        int: the exit code. Returns 1 if the Python version installed is
        below 3.6.

    """
    if sys.version_info.major < 3 or sys.version_info.minor < 6:
        logging.critical(_("Whoops! opsdroid requires python 3.6 or above."))
        sys.exit(1)


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
            _("'welcome-message: true/false' is missing in configuration.yaml")
        )
