"""Helper functions to use within OpsDroid."""

import logging


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
