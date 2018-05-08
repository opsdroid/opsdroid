"""Constants used by OpsDroid."""
import os
from appdirs import user_log_dir, user_config_dir, user_data_dir
from opsdroid import __version__  # noqa # pylint: disable=unused-import

NAME = 'opsdroid'
DEFAULT_GIT_URL = "https://github.com/opsdroid/"
MODULES_DIRECTORY = "opsdroid-modules"
DEFAULT_ROOT_PATH = user_data_dir(NAME)
DEFAULT_LOG_FILENAME = os.path.join(
    user_log_dir(NAME, appauthor=False), 'output.log')
DEFAULT_MODULES_PATH = user_data_dir(NAME, MODULES_DIRECTORY)
DEFAULT_MODULE_DEPS_PATH = os.path.join(
    user_data_dir(NAME, MODULES_DIRECTORY), "site-packages")
DEFAULT_CONFIG_PATH = os.path.join(
    user_config_dir(NAME, appauthor=False), "configuration.yaml")
PRE_0_12_0_CONFIG_PATH = os.path.join(DEFAULT_ROOT_PATH, "configuration.yaml")
PRE_0_12_0_ROOT_PATH = os.path.expanduser("~/.opsdroid")
DEFAULT_MODULE_BRANCH = "master"
DEFAULT_LANGUAGE = 'en'
LOCALE_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'locale')
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
WITAI_API_ENDPOINT = "https://api.wit.ai/message?"

RECASTAI_API_ENDPOINT = "https://api.recast.ai/v2/request"
