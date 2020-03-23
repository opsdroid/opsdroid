"""Constants used by OpsDroid."""
import os
from appdirs import user_log_dir, user_config_dir, user_data_dir
import opsdroid
from opsdroid import __version__  # noqa # pylint: disable=unused-import

NAME = "opsdroid"
MODULE_ROOT = os.path.dirname(os.path.abspath(opsdroid.__file__))
DEFAULT_GIT_URL = "https://github.com/opsdroid/"
MODULES_DIRECTORY = "opsdroid-modules"
DEFAULT_ROOT_PATH = user_data_dir(NAME)
DEFAULT_LOG_FILENAME = os.path.join(user_log_dir(NAME, appauthor=False), "output.log")
DEFAULT_MODULES_PATH = user_data_dir(NAME, MODULES_DIRECTORY)
DEFAULT_MODULE_DEPS_PATH = os.path.join(
    user_data_dir(NAME, MODULES_DIRECTORY), "site-packages"
)
DEFAULT_CONFIG_PATH = os.path.join(
    user_config_dir(NAME, appauthor=False), "configuration.yaml"
)
DEFAULT_CONFIG_LOCATIONS = [
    "configuration.yaml",
    DEFAULT_CONFIG_PATH,
    "/etc/opsdroid/configuration.yaml",
]
DEFAULT_MODULE_BRANCH = "master"
DEFAULT_LANGUAGE = "en"
LOCALE_DIR = os.path.join(MODULE_ROOT, "locale")
EXAMPLE_CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "configuration/example_configuration.yaml",
)
REGEX_PARSE_SCORE_FACTOR = 0.6

RASANLU_DEFAULT_URL = "http://localhost:5000"
RASANLU_DEFAULT_PROJECT = "opsdroid"

LUISAI_DEFAULT_URL = "https://westus.api.cognitive.microsoft.com/luis/v2.0/apps/"

DIALOGFLOW_API_ENDPOINT = "https://api.dialogflow.com/v1/query"
DIALOGFLOW_API_VERSION = "20150910"

WITAI_DEFAULT_VERSION = "20170307"
WITAI_API_ENDPOINT = "https://api.wit.ai/message?"

SAPCAI_API_ENDPOINT = "https://api.cai.tools.sap/v2/request"

WATSON_API_ENDPOINT = "https://{gateway}.watsonplatform.net/assistant/api"
WATSON_API_VERSION = "2019-02-28"
ENV_VAR_REGEX = r"^\"?\${?(?=\_?[A-Z])([A-Z-_]+)}?\"?$"
