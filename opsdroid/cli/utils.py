"""Utilities for the opsdroid CLI commands."""

import click
import contextlib
import gettext
import os
import logging
import subprocess
import sys
import time

from opsdroid.core import OpsDroid
from opsdroid.configuration import load_config_file
from opsdroid.const import (
    LOCALE_DIR,
    DEFAULT_LANGUAGE,
    DEFAULT_CONFIG_PATH,
    DEFAULT_CONFIG_LOCATIONS,
)
from opsdroid.helper import get_config_option
from opsdroid.loader import Loader
from opsdroid.logging import configure_logging


_LOGGER = logging.getLogger("opsdroid")

path_option = click.option(
    "-f",
    "path",
    help="Load a configuration from a path instead of using the default location.",
    type=click.Path(exists=True),
)


def edit_config(ctx, path):
    """Open config/log file with favourite editor.

    Args:
        ctx (:obj:`click.Context`): The current click cli context.
        path (str or None): the path passed to the config option.
        value (string): the value of this parameter after invocation.

    Returns:
        int: the exit code. Always returns 0 in this case.

    """
    file = path or DEFAULT_CONFIG_PATH
    editor = os.environ.get("EDITOR", "vi")

    if editor == "vi":
        click.echo(
            "You are about to edit a file in vim. \n"
            "Read the tutorial on vim at: https://bit.ly/2HRvvrB"
        )
        time.sleep(1.5)

    subprocess.run([editor, file])
    ctx.exit(0)


def validate_config(ctx, path):
    """Validate opsdroid configuration.

    We load the configuration and modules from it to run the validation on them.
    Only modules that contain the constant variable `CONFIG_SCHEMA` will be validated
    the ones without it will just be silent.

    Note that if the path doesn't exist or is a bad one click will throw an error telling
    you that the path doesn't exist. Also, the file needs to be either a json or a yaml file.


    Args:
        ctx (:obj:`click.Context`): The current click cli context.
        path (string): a string representing the path to load the config,
            obtained from `ctx.obj`.
        value (string): the value of this parameter after invocation.
            It is either "config" or "log" depending on the program
            calling this function.

    Returns:
        int: the exit code. Always returns 0 in this case.

    """
    with OpsDroid() as opsdroid:
        loader = Loader(opsdroid)

        config = load_config_file([path] if path else DEFAULT_CONFIG_LOCATIONS)

        loader.load_modules_from_config(config)
        click.echo("Configuration validated - No errors founds!")

        ctx.exit(0)


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
        below 3.7.

    """
    if sys.version_info.major < 3 or sys.version_info.minor < 7:
        logging.critical(_("Whoops! opsdroid requires python 3.7 or above."))
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
                    "You can customise your opsdroid by modifying your configuration.yaml."
                )
            )
            _LOGGER.info(
                _("Read more at: http://opsdroid.readthedocs.io/#configuration")
            )
            _LOGGER.info(_("Watch the Get Started Videos at: http://bit.ly/2fnC0Fh"))
            _LOGGER.info(
                _(
                    "Install Opsdroid Desktop at: \n"
                    "https://github.com/opsdroid/opsdroid-desktop/releases"
                )
            )
            _LOGGER.info("=" * 40)
    except KeyError:
        _LOGGER.warning(
            _("'welcome-message: true/false' is missing in configuration.yaml")
        )


def list_all_modules(ctx, path):
    """List the active modules from config.

    This function will try to get information from the modules that are active in the
    configuration file and print them as a table or will just print a sentence saying that
    there are no active modules for that type.

    Args:
        ctx (:obj:`click.Context`): The current click cli context.
        path (str): a str that contains a path passed.

    Returns:
        int: the exit code. Always returns 0 in this case.

    """
    config = load_config_file([path] if path else DEFAULT_CONFIG_LOCATIONS)

    click.echo(
        click.style(
            f"{'NAME':15} {'TYPE':15} {'MODE':15} {'CACHED':15}  {'LOCATION':15}",
            fg="blue",
            bold=True,
        )
    )
    for module_type, module in config.items():
        if module_type in ("connectors", "databases", "parsers", "skills"):
            for name, options in module.items():

                mode = get_config_option(
                    ["repo", "path", "gist"], options, True, "module"
                )
                cache = get_config_option(["no-cache"], options, "no", "yes")
                location = get_config_option(
                    ["repo", "path", "gist"],
                    options,
                    True,
                    f"opsdroid.{module_type}.{name}",
                )

                click.echo(
                    f"{name:15} {module_type:15} {mode[1]:15} {cache[0]:15}  {location[2]:15}"
                )

    ctx.exit(0)


def build_config(ctx, params):
    """Load configuration, load modules and install dependencies.

    This function loads the configuration and install all necessary
    dependencies defined on a `requirements.txt` file inside the module.
    If the flag `--verbose` is passed the logging level will be set as debug and
    all logs will be shown to the user.


    Args:
        ctx (:obj:`click.Context`): The current click cli context.
        params (dict): a dictionary of all parameters pass to the click
            context when invoking this function as a callback.

    Returns:
        int: the exit code. Always returns 0 in this case.

    """
    click.echo("Opsdroid will build modules from config.")
    path = params.get("path")

    with contextlib.suppress(Exception):
        check_dependencies()

        config = load_config_file([path] if path else DEFAULT_CONFIG_LOCATIONS)

        if params["verbose"]:
            config["logging"] = {"level": "debug"}
            configure_logging(config)

        with OpsDroid(config=config) as opsdroid:

            opsdroid.loader.load_modules_from_config(config)

            click.echo(click.style("SUCCESS:", bg="green", bold=True), nl=False)
            click.echo(" Opsdroid modules successfully built from config.")
