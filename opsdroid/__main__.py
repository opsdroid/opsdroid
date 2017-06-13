"""Starts opsdroid."""

import os
import sys
import logging
import argparse

from opsdroid.core import OpsDroid
from opsdroid.const import DEFAULT_LOG_FILENAME, EXAMPLE_CONFIG_FILE
from opsdroid.web import Web


_LOGGER = logging.getLogger("opsdroid")


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

    try:
        if not config["logging"]["console"]:
            console_handler.setLevel(logging.CRITICAL)
    except KeyError:
        pass

    if logfile_path:
        file_handler = logging.FileHandler(logfile_path)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        rootlogger.addHandler(file_handler)

    _LOGGER.info("="*40)
    _LOGGER.info("Stated application")


def get_logging_level(logging_level):
    """Get the logger level based on the user configuration."""
    if logging_level == 'critical':
        return logging.CRITICAL
    elif logging_level == 'error':
        return logging.ERROR
    elif logging_level == 'warning':
        return logging.WARNING
    elif logging_level == 'debug':
        return logging.DEBUG

    return logging.INFO


def parse_args(args):
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run opsdroid.')
    parser.add_argument('--gen-config', action="store_true",
                        help='prints out an example configuration file')
    return parser.parse_args(args)


def check_dependencies():
    """Check for system dependencies required by opsdroid."""
    if sys.version_info[0] < 3 or sys.version_info[1] < 5:
        logging.critical("Whoops! opsdroid requires python 3.5 or above.")
        sys.exit(1)


def main():
    """Enter the application here."""
    args = parse_args(sys.argv[1:])

    if args.gen_config:
        with open(EXAMPLE_CONFIG_FILE, 'r') as conf:
            print(conf.read())
        sys.exit(0)

    check_dependencies()

    restart = True

    while restart:
        with OpsDroid() as opsdroid:
            opsdroid.load()
            configure_logging(opsdroid.config)
            opsdroid.web_server = Web(opsdroid)
            opsdroid.start_loop()
            restart = opsdroid.should_restart


if __name__ == "__main__":
    main()
