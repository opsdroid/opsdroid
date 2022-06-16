"""Class for Filter logs and logging logic."""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from rich.logging import RichHandler

from opsdroid.const import DEFAULT_LOG_FILENAME, __version__

_LOGGER = logging.getLogger(__name__)


class ParsingFilter(logging.Filter):
    """Class that filters logs."""

    def __init__(self, config, *parse_list):
        """Create object to implement filtering."""
        super(ParsingFilter, self).__init__()
        self.config = config
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


def set_formatter_string(config: dict):
    """Set the formatter string dependending on the config.

    Currently our logs allow you to pass different configuration parameters to
    format the logs that are returned to us. This is a helper function to handle
    these cases.

    Args:
        config: contains only the logging section of the configuration since we
            don't care about anything else for logs.

    """
    formatter_str = "%(levelname)s %(name)s"

    if config.get("formatter"):
        return config["formatter"]

    if config.get("extended"):
        formatter_str += ".%(funcName)s():"

    if config.get("timestamp"):
        formatter_str = "%(asctime)s " + formatter_str

    formatter_str += " %(message)s"

    return formatter_str


def configure_logging(config):
    """Configure the root logger based on user config."""
    rootlogger = logging.getLogger()
    while rootlogger.handlers:
        rootlogger.handlers.pop()

    try:
        if config["path"]:
            logfile_path = os.path.expanduser(config["path"])
        else:
            logfile_path = config["path"]
    except KeyError:
        logfile_path = DEFAULT_LOG_FILENAME

    if logfile_path:
        logdir = os.path.dirname(os.path.realpath(logfile_path))
        if not os.path.isdir(logdir):
            os.makedirs(logdir)

    log_level = get_logging_level(config.get("level", "info"))
    rootlogger.setLevel(log_level)
    formatter_str = set_formatter_string(config)
    formatter = logging.Formatter(formatter_str)
    handler = None

    if config.get("rich") is not False:
        handler = RichHandler(
            rich_tracebacks=True,
            show_time=config.get("timestamp", True),
            show_path=config.get("extended", True),
        )

    if logfile_path:
        file_handler = RotatingFileHandler(
            logfile_path, maxBytes=config.get("file-size", 50e6)
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        rootlogger.addHandler(file_handler)

    # If we are running in a non-interactive shell (without a tty)
    # then use simple logging instead of rich logging
    # Config value always overrides
    running_in_non_interactive_shell = False
    console = config.get("test_logging_console", sys.stderr)
    if config.get("console") is True:
        handler = logging.StreamHandler(stream=console)
        handler.setFormatter(formatter)
    else:
        if config.get("console") is None and not console.isatty():
            running_in_non_interactive_shell = True
            handler = logging.StreamHandler(stream=console)
            handler.setFormatter(formatter)

    # If we still don't have the handler, we are assuming that
    # the user wants to switch off logging, let's log only
    # Critical errors
    if not handler:
        handler = logging.StreamHandler(stream=console)
        handler.setFormatter(formatter)
        log_level = get_logging_level("critical")

    if config.get("filter") and handler:
        handler.addFilter(ParsingFilter(config, config["filter"]))
    if handler:
        handler.setLevel(log_level)
        rootlogger.addHandler(handler)

    _LOGGER.info("=" * 40)
    _LOGGER.info(_("Started opsdroid %s."), __version__)
    if running_in_non_interactive_shell:
        _LOGGER.warning(
            "Running in non-interactive shell - falling back to simple logging. You can override this using 'logging.config: false'"
        )


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
