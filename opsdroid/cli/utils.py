"""Utilities for the opsdroid CLI commands."""

import click
import gettext
import os
import logging
import subprocess
import sys
import time
import warnings

from opsdroid.const import (
    DEFAULT_LOG_FILENAME,
    LOCALE_DIR,
    DEFAULT_LANGUAGE,
    DEFAULT_CONFIG_PATH,
)

_LOGGER = logging.getLogger("opsdroid")


def edit_files(ctx, param, value):
    """Open config/log file with favourite editor."""
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
    """Check for system dependencies required by opsdroid."""
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
