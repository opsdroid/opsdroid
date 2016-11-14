"""Starts opsdroid."""

import sys
import os
import logging
import argparse

from opsdroid.core import OpsDroid
from opsdroid.helper import set_logging_level
from opsdroid.const import LOG_FILENAME


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
    """The main function."""
    logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO)
    logging.info("="*40)
    logging.info("Stated application")

    args = parse_args(sys.argv[1:])

    if args.gen_config:
        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "configuration/example_configuration.yaml")
        with open(path, 'r') as conf:
            print(conf.read())
        sys.exit(0)

    check_dependencies()

    with OpsDroid() as opsdroid:
        opsdroid.load()
        if "logging" in opsdroid.config:
            set_logging_level(opsdroid.config['logging'])
        opsdroid.start_loop()
        opsdroid.exit()


if __name__ == "__main__":
    main()
