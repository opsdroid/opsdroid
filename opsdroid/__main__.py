"""Starts opsdroid."""

import logging

from opsdroid.loader import Loader
from opsdroid.core import OpsDroid
from opsdroid.helper import set_logging_level
from opsdroid.const import LOG_FILENAME


def main():
    """The main function."""
    logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO)
    logging.info("="*40)
    logging.info("Stated application")
    with OpsDroid() as opsdroid:
        loader = Loader(opsdroid)
        opsdroid.config = loader.load_config_file("./configuration.yaml")
        if "logging" in opsdroid.config:
            set_logging_level(opsdroid.config['logging'])
        loader.load_config(opsdroid.config)
        opsdroid.exit()

if __name__ == "__main__":
    main()
