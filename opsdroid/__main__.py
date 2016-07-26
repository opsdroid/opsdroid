import sys
import json
import logging

from opsdroid.loader import Loader
from opsdroid.core import OpsDroid
from opsdroid.helper import *

LOG_FILENAME = 'output.log'

def main():
    """ The main function """
    opsdroid = OpsDroid()
    loader = Loader(opsdroid)
    opsdroid.config = loader.load_config_file("./configuration.yaml")
    set_logging_level(opsdroid.config['logging'])
    loader.load_config(opsdroid.config)
    return opsdroid

if __name__ == "__main__":
    logging.basicConfig(filename=LOG_FILENAME,level=logging.INFO)
    logging.info("="*40)
    logging.info("Stated application")
    opsdroid = main()
    opsdroid.exit()
