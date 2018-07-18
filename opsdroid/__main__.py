"""Starts opsdroid."""

import os
import subprocess
import sys
import logging
import gettext
import time
import contextlib

import click

from opsdroid import __version__
from opsdroid.core import OpsDroid
from opsdroid.web import Web
from opsdroid.const import DEFAULT_LOG_FILENAME, LOCALE_DIR, \
    EXAMPLE_CONFIG_FILE, DEFAULT_LANGUAGE, DEFAULT_CONFIG_PATH


gettext.install('opsdroid')
_LOGGER = logging.getLogger("opsdroid")


def configure_lang(config):
    """Configure app language based on user config.

    Args:
        config: Language Configuration and it uses ISO 639-1 code.
        for more info https://en.m.wikipedia.org/wiki/List_of_ISO_639-1_codes


    """
    lang_code = config.get("lang", DEFAULT_LANGUAGE)
    if lang_code != DEFAULT_LANGUAGE:
        lang = gettext.translation(
            'opsdroid', LOCALE_DIR, (lang_code,), fallback=True)
        lang.install()


def configure_logging(config):
    """Configure the root logger based on user config."""
    rootlogger = logging.getLogger()
    while rootlogger.handlers:
        rootlogger.handlers.pop()

    try:
        if config["logging"]["path"]:
            logfile_path = os.path.expanduser(config["logging"]["path"])
        else:
            logfile_path = config["logging"]["path"]
    except KeyError:
        logfile_path = DEFAULT_LOG_FILENAME

    try:
        log_level = get_logging_level(
            config["logging"]["level"])
    except KeyError:
        log_level = logging.INFO

    rootlogger.setLevel(log_level)
    formatter = logging.Formatter('%(levelname)s %(name)s: %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    rootlogger.addHandler(console_handler)

    with contextlib.suppress(KeyError):
        if not config["logging"]["console"]:
            console_handler.setLevel(logging.CRITICAL)

    if logfile_path:
        logdir = os.path.dirname(os.path.realpath(logfile_path))
        if not os.path.isdir(logdir):
            os.makedirs(logdir)
        file_handler = logging.FileHandler(logfile_path)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        rootlogger.addHandler(file_handler)
    _LOGGER.info("="*40)
    _LOGGER.info(_("Started application"))


def get_logging_level(logging_level):
    """Get the logger level based on the user configuration."""
    if logging_level == 'critical':
        return logging.CRITICAL

    if logging_level == 'error':
        return logging.ERROR
    if logging_level == 'warning':
        return logging.WARNING

    if logging_level == 'debug':
        return logging.DEBUG

    return logging.INFO


def check_dependencies():
    """Check for system dependencies required by opsdroid."""
    if sys.version_info.major < 3 or sys.version_info.minor < 5:
        logging.critical(_("Whoops! opsdroid requires python 3.5 or above."))
        sys.exit(1)


def print_version(ctx, param, value):
    """Print out the version of opsdroid that is installed."""
    if not value or ctx.resilient_parsing:
        return
    click.echo('opsdroid v{version}'.format(version=__version__))
    ctx.exit(0)


def print_example_config(ctx, param, value):
    """Print out the example config."""
    if not value or ctx.resilient_parsing:
        return
    with open(EXAMPLE_CONFIG_FILE, 'r') as conf:
        click.echo(conf.read())
    ctx.exit(0)


def edit_files(ctx, param, value):
    """Open config/log file with favourite editor."""
    if value == 'config':
        file = DEFAULT_CONFIG_PATH
    elif value == 'log':
        file = DEFAULT_LOG_FILENAME
    else:
        return

    editor = os.environ.get('EDITOR', 'vi')
    if editor == 'vi':
        click.echo('You are about to edit a file in vim. \n'
                   'Read the tutorial on vim at: https://bit.ly/2HRvvrB')
        time.sleep(3)

    subprocess.run([editor, file])
    ctx.exit(0)


def welcome_message(config):
    """Add welcome message if set to true in configuration."""
    try:
        if config['welcome-message']:
            _LOGGER.info("=" * 40)
            _LOGGER.info(_("You can customise your opsdroid by modifying "
                           "your configuration.yaml"))
            _LOGGER.info(_("Read more at: "
                           "http://opsdroid.readthedocs.io/#configuration"))
            _LOGGER.info(_("Watch the Get Started Videos at: "
                           "http://bit.ly/2fnC0Fh"))
            _LOGGER.info(_("Install Opsdroid Desktop at: \n"
                           "https://github.com/opsdroid/opsdroid-desktop/"
                           "releases"))
            _LOGGER.info("=" * 40)
    except KeyError:
        _LOGGER.warning(_("'welcome-message: true/false' is missing in "
                          "configuration.yaml"))


@click.command()
@click.option('--gen-config', is_flag=True, callback=print_example_config,
              expose_value=False, default=False,
              help='Print an example config and exit.')
@click.option('--version', '-v', is_flag=True, callback=print_version,
              expose_value=False, default=False, is_eager=True,
              help='Print the version and exit.')
@click.option('--edit-config', '-e', is_flag=True, callback=edit_files,
              default=False, flag_value='config', expose_value=False,
              help='Opens configuration.yaml with your favorite editor'
                   ' and exits.')
@click.option('--view-log', '-l', is_flag=True, callback=edit_files,
              default=False, flag_value='log', expose_value=False,
              help='Opens opsdroid logs with your favorite editor'
                   ' and exits.')
def main():
    """Opsdroid is a chat bot framework written in Python.

    It is designed to be extendable, scalable and simple.
    See https://opsdroid.github.io/ for more information.
    """
    check_dependencies()

    with OpsDroid() as opsdroid:
        opsdroid.load()
        configure_lang(opsdroid.config)
        configure_logging(opsdroid.config)
        welcome_message(opsdroid.config)
        opsdroid.web_server = Web(opsdroid)
        opsdroid.start_loop()


def init():
    """Enter the application."""
    if __name__ == "__main__":
        main()


init()
