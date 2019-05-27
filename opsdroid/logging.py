import os
import logging
import contextlib

from opsdroid.const import DEFAULT_LOG_FILENAME, __version__

_LOGGER = logging.getLogger(__name__)


class ParsingFilter(logging.Filter):
    def __init__(self, config, *parse_list):
        self.config = config["logging"]
        self.parse_list = parse_list[0].get("whitelist") or parse_list[0].get(
            "blacklist"
        )

        self.parse_list = [logging.Filter(name) for name in self.parse_list]

    def filter(self, record):
        if self.config["filter"].get("whitelist", None):
            return any(name.filter(record) for name in self.parse_list)
        return not any(name.filter(record) for name in self.parse_list)


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
        log_level = get_logging_level(config["logging"]["level"])
    except KeyError:
        log_level = logging.INFO

    rootlogger.setLevel(log_level)

    if config["logging"].get("extended"):
        formatter = logging.Formatter(
            "%(levelname)s %(name)s.%(funcName)s(): %(message)s"
        )
    else:
        formatter = logging.Formatter("%(levelname)s %(name)s: %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    if config["logging"].get("filter", None):
        console_handler.addFilter(ParsingFilter(config, config["logging"]["filter"]))

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

        if config["logging"].get("filter", None):
            file_handler.addFilter(ParsingFilter(config, config["logging"]["filter"]))

        rootlogger.addHandler(file_handler)
    _LOGGER.info("=" * 40)
    _LOGGER.info(_("Started opsdroid %s"), __version__)
    _LOGGER.info(config["logging"])


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
