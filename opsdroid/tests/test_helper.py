import os
import datetime
import tempfile

from opsdroid.helper import (
    del_rw,
    file_is_ipython_notebook,
    convert_ipynb_to_script,
    extract_gist_id,
    get_opsdroid,
    JSONEncoder,
    JSONDecoder,
    convert_dictionary,
    get_config_option,
    get_parser_config,
)


class TestHelper:
    """Test the opsdroid helper classes."""

    def test_del_rw(self, mocker):
        mock_chmod = mocker.patch("os.chmod")
        mock_remove = mocker.patch("os.remove")
        del_rw(None, None, None)
        assert mock_chmod.called is True
        assert mock_remove.called is True

    def test_file_is_ipython_notebook(self):
        assert file_is_ipython_notebook("test.ipynb") is True
        assert file_is_ipython_notebook("test.py") is False

    def test_convert_ipynb_to_script(self):
        notebook_path = os.path.abspath(
            "opsdroid/testing/mockmodules/skills/test_notebook.ipynb"
        )

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as output_file:
            convert_ipynb_to_script(notebook_path, output_file.name)
            assert os.path.getsize(output_file.name) > 0

    def test_extract_gist_id(self):
        assert (
            extract_gist_id(
                "https://gist.github.com/jacobtomlinson/"
                "c9852fa17d3463acc14dca1217d911f6"
            )
            == "c9852fa17d3463acc14dca1217d911f6"
        )

        assert (
            extract_gist_id("c9852fa17d3463acc14dca1217d911f6")
            == "c9852fa17d3463acc14dca1217d911f6"
        )

    def test_opsdroid(self):
        # Test that get_opsdroid returns None if no instances exist
        assert get_opsdroid() is None

    def test_convert_dictionary(self):
        modules = [
            {"name": "telegram", "access-token": "test"},
            {"name": "mattermost", "api-token": "test"},
        ]
        updated_modules = convert_dictionary(modules)
        assert updated_modules["telegram"].get("token") == "test"
        assert "token" in updated_modules["mattermost"]

    def test_get_config_option(self):
        module_config = {"repo": "test"}

        result = get_config_option(
            ["repo", "path", "gist"],
            module_config,
            True,
            "opsdroid.connectors.websocket",
        )

        assert result == (True, "repo", "test")

    def test_get_config_no_option(self):
        module_config = {
            "bot-name": "mybot",
            "max-connections": 10,
            "connection-timeout": 10,
        }

        result = get_config_option(
            ["repo", "path", "gist"], module_config, True, "module"
        )

        assert result == ("module", "module", "module")

    def test_get_config_option_exception(self):
        module_config = None

        result = get_config_option(
            ["repo", "path", "gist"], module_config, True, "module"
        )
        assert result == ("module", "module", "module")


class TestJSONEncoder:
    """A JSON Encoder test class.

    Test the custom json encoder class.

    """

    def test_datetime_to_dict(self):
        """Test default of json encoder class.

        This method will test the conversion of the datetime
        object to dict.

        """
        type_cls = datetime.datetime
        test_obj = datetime.datetime(2018, 10, 2, 0, 41, 17, 74644)
        encoder = JSONEncoder()
        obj = encoder.default(o=test_obj)
        assert {
            "__class__": type_cls.__name__,
            "year": 2018,
            "month": 10,
            "day": 2,
            "hour": 0,
            "minute": 41,
            "second": 17,
            "microsecond": 74644,
        } == obj


class TestJSONDecoder:
    """A JSON Decoder test class.

    Test the custom json decoder class.

    """

    def test_dict_to_datetime(self):
        """Test call of json decoder class.

        This method will test the conversion of the dict to
        datetime object.

        """
        test_obj = {
            "__class__": datetime.datetime.__name__,
            "year": 2018,
            "month": 10,
            "day": 2,
            "hour": 0,
            "minute": 41,
            "second": 17,
            "microsecond": 74644,
        }
        decoder = JSONDecoder()
        obj = decoder(test_obj)
        assert datetime.datetime(2018, 10, 2, 0, 41, 17, 74644) == obj

    def test_get_parser_config(self):
        parsers = [
            {
                "name": "dialogflow",
                "module": "",
                "config": {
                    "name": "dialogflow",
                    "module": "",
                    "project-id": "test-ddd33",
                    "type": "parsers",
                    "enabled": True,
                    "entrypoint": None,
                    "is_builtin": "",
                    "module_path": "opsdroid.parsers.dialogflow",
                    "install_path": "",
                    "branch": "master",
                },
                "intents": None,
            },
            {
                "name": "regex",
                "module": "",
                "config": {
                    "name": "regex",
                    "module": "",
                    "type": "parsers",
                    "enabled": True,
                    "entrypoint": None,
                    "is_builtin": "",
                    "module_path": "opsdroid.parsers.regex",
                    "install_path": "",
                    "branch": "master",
                },
                "intents": None,
            },
        ]

        dialogflow_config = get_parser_config("dialogflow", parsers)

        assert dialogflow_config
        assert dialogflow_config["name"] == "dialogflow"

    def test_get_parser_config_none(self):
        parsers = {}

        config = get_parser_config("dialogflow", parsers)

        assert not config
