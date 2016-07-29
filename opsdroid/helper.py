"""Helper functions to use within OpsDroid."""

import logging
import re
import subprocess

from opsdroid.const import MODULES_DIRECTORY


def set_logging_level(logging_level):
    """Set the logger level based on the user configuration."""
    logger = logging.getLogger()
    if logging_level == 'critical':
        logger.setLevel(logging.CRITICAL)
    elif logging_level == 'error':
        logger.setLevel(logging.ERROR)
    elif logging_level == 'warning':
        logger.setLevel(logging.WARNING)
    elif logging_level == 'info':
        logger.setLevel(logging.INFO)
    elif logging_level == 'debug':
        logger.setLevel(logging.DEBUG)
        # No need to log the others as they'll never be seen
        logging.debug("Set log level to debug")
    else:
        logger.setLevel(logging.INFO)
        logging.warning("Log level '" + logging_level +
                        "' unknown, defaulting to 'info'")


def build_module_path(mod_type, mod_name):
    """Generate the module path from name and type."""
    return MODULES_DIRECTORY + "." + mod_type + "." + mod_name


def match(regex, message):
    """Regex match a string."""
    return re.match(regex, message, re.M | re.I)


def git_clone(git_url, install_path, branch):
    """Clone a git repo to a location and wait for finish."""
    process = subprocess.Popen(["git", "clone", "-b", branch,
                                git_url, install_path], shell=False,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    process.wait()
