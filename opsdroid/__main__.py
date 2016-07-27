""" Starts OpsDroid """

import sys
import json
import logging

from opsdroid.loader import Loader
from opsdroid.core import OpsDroid
from opsdroid.helper import *
from opsdroid.const import LOG_FILENAME


def main():
    """ The main function """
    opsdroid = OpsDroid()
    loader = Loader(opsdroid)
    opsdroid.config = loader.load_config_file("./configuration.yaml")
    if "logging" in opsdroid.config:
        set_logging_level(opsdroid.config['logging'])
    loader.load_config(opsdroid.config)
    return opsdroid

if __name__ == "__main__":
    logging.basicConfig(filename=LOG_FILENAME,level=logging.INFO)
    logging.info("="*40)
    logging.info("Stated application")
    opsdroid = main()
    opsdroid.exit()
