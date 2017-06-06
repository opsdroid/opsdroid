"""Constants used by OpsDroid."""
import os

__version__ = "0.8.1"

LOG_FILENAME = 'output.log'
DEFAULT_GIT_URL = "https://github.com/opsdroid/"
MODULES_DIRECTORY = "opsdroid-modules"
DEFAULT_ROOT_PATH = os.path.join(os.path.expanduser("~"), ".opsdroid")
DEFAULT_MODULES_PATH = os.path.join(DEFAULT_ROOT_PATH, "modules")
DEFAULT_MODULE_DEPS_PATH = os.path.join(DEFAULT_ROOT_PATH, "site-packages")
DEFAULT_CONFIG_PATH = os.path.join(DEFAULT_ROOT_PATH, "configuration.yaml")
DEFAULT_MODULE_BRANCH = "master"
EXAMPLE_CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "configuration/example_configuration.yaml")
