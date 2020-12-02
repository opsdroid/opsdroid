"""Class for Filter logs and logging logic."""

import os
import logging
import contextlib

from logging.handlers import RotatingFileHandler
from opsdroid.const import DEFAULT_LOG_FILENAME, __version__

_LOGGER = logging.getLogger(__name__)


class ParsingFilter(logging.Filter):
    """Class that filters logs."""

    def __init__(self, config, *parse_list):
        """Create object to implement filtering."""
        super(ParsingFilter, self).__init__()
        self.config = config["logging"]
        try:
            if (
                self.config["filter"]["whitelist"]
                and self.config["filter"]["blacklist"]
            ):
                _LOGGER.warning(
                    _(
                        "Both whitelist and blacklist filters found in configuration. "
                        "Only one can be used at a time - only the whitelist filter will be used."
                    )
                )
                self.parse_list = [
                    logging.Filter(name) for name in parse_list[0]["whitelist"]
                ]
        except KeyError:
            self.parse_list = parse_list[0].get("whitelist") or parse_list[0].get(
                "blacklist"
            )

            self.parse_list = [logging.Filter(name) for name in self.parse_list]

    def filter(self, record):
        """Apply filter to the log message.

        This is a subset of Logger.filter, this method applies the logger
        filters and returns a bool. If the value is true the record will
        be passed to the handlers and the log shown. If the value is
        false it will be ignored.

        Args:
            record: a log record containing the log message and the
                name of the log - example: opsdroid.core.

        Returns:
            Boolean: If True - pass the log to handler.

        """

        if self.config["filter"].get("whitelist"):
            return any(name.filter(record) for name in self.parse_list)
        return not any(name.filter(record) for name in self.parse_list)


def configure_logging(config):
    """Configure the root logger based on user config."""
    rootlogger = logging.getLogger()
    logging_config = config or {}

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
        log_level = get_logging_level(config["logging"]["level"])
    except KeyError:
        log_level = logging.INFO

    rootlogger.setLevel(log_level)

    formatter_str = "%(levelname)s %(name)s:"

    with contextlib.suppress(KeyError):
        if config["logging"]["timestamp"]:
            formatter_str = "%(asctime)s " + formatter_str

    with contextlib.suppress(KeyError):
        if config["logging"]["extended"]:
            formatter_str = formatter_str[:-1] + ".%(funcName)s():"

    formatter_str += " %(message)s"
    formatter = logging.Formatter(formatter_str)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    with contextlib.suppress(KeyError):
        console_handler.addFilter(ParsingFilter(config, config["logging"]["filter"]))

    rootlogger.addHandler(console_handler)

    with contextlib.suppress(KeyError):
        if not config["logging"]["console"]:
            console_handler.setLevel(logging.CRITICAL)

    if logfile_path:
        logdir = os.path.dirname(os.path.realpath(logfile_path))
        if not os.path.isdir(logdir):
            os.makedirs(logdir)

        file_handler = RotatingFileHandler(
            logfile_path, maxBytes=logging_config.get("file-size", 50e6)
        )

        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)

        with contextlib.suppress(KeyError):
            file_handler.addFilter(ParsingFilter(config, config["logging"]["filter"]))

        rootlogger.addHandler(file_handler)
    _LOGGER.info("=" * 40)
    _LOGGER.info(_("Started opsdroid %s."), __version__)


def get_logging_level(logging_level):
    """Get the logger level based on the user configuration.

    Args:
        logging_level: logging level from config file

    Returns:
        logging LEVEL ->
            CRITICAL = 50
            FATAL = CRITICAL
            ERROR = 40
            WARNING = 30
            WARN = WARNING
            INFO = 20
            DEBUG = 10
            NOTSET = 0

    """
    if logging_level == "critical":
        return logging.CRITICAL

    if logging_level == "error":
        return logging.ERROR
    if logging_level == "warning":
        return logging.WARNING

    if logging_level == "debug":
        return logging.DEBUG

    return logging.INFO
