"""Constants used by OpsDroid."""
import os

__version__ = "0.11.2"

DEFAULT_GIT_URL = "https://github.com/opsdroid/"
MODULES_DIRECTORY = "opsdroid-modules"
DEFAULT_ROOT_PATH = os.path.expanduser("~/.opsdroid")
DEFAULT_LOG_FILENAME = os.path.join(DEFAULT_ROOT_PATH, 'output.log')
DEFAULT_MODULES_PATH = os.path.join(DEFAULT_ROOT_PATH, "modules")
DEFAULT_MODULE_DEPS_PATH = os.path.join(DEFAULT_ROOT_PATH, "site-packages")
DEFAULT_CONFIG_PATH = os.path.join(DEFAULT_ROOT_PATH, "configuration.yaml")
DEFAULT_MODULE_BRANCH = "master"
DEFAULT_LANGUAGE = 'en'
EXAMPLE_CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "configuration/example_configuration.yaml")
REGEX_MAX_SCORE = 0.6

RASANLU_DEFAULT_URL = "http://localhost:5000"
RASANLU_DEFAULT_PROJECT = "opsdroid"

LUISAI_DEFAULT_URL = "https://westus.api.cognitive.microsoft.com" \
                     "/luis/v2.0/apps/"

DIALOGFLOW_API_ENDPOINT = "https://api.dialogflow.com/v1/query"
DIALOGFLOW_API_VERSION = "20150910"

WITAI_DEFAULT_VERSION = "20170307"
