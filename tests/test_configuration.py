import os
import shutil

import tempfile
import contextlib
import unittest
import unittest.mock as mock

from opsdroid.core import OpsDroid
from opsdroid.cli.start import configure_lang
from opsdroid import loader as ld
from opsdroid.configuration import (
    create_default_config,
    load_config_file,
    validate_data_type,
)
from opsdroid.helper import del_rw


class TestConfiguration(unittest.TestCase):
    """Test the opsdroid loader class."""

    def setup(self):
        configure_lang({})
        opsdroid = mock.MagicMock()
        loader = ld.Loader(opsdroid)
        return opsdroid, loader

    def setUp(self):
        os.umask(000)
        self._tmp_dir = os.path.join(tempfile.gettempdir(), "opsdroid_tests")
        with contextlib.suppress(FileExistsError):
            os.makedirs(self._tmp_dir, mode=0o777)

    def tearDown(self):
        shutil.rmtree(self._tmp_dir, onerror=del_rw)

    def test_schema(self):
        skill_path = "opsdroid/testing/mockmodules/skills/schema_skill"
        example_config = {
            "connectors": {"websocket": {}},
            "skills": {"test": {"path": skill_path}},
        }
        with OpsDroid(config=example_config) as opsdroid:
            opsdroid.sync_load()
            assert opsdroid.skills
            assert len(opsdroid.skills) == 1
            assert "foo" in opsdroid.skills[0].config
            assert opsdroid.skills[0].config["foo"] == "bar"

    def test_load_config_file(self):
        config = load_config_file([os.path.abspath("tests/configs/minimal.yaml")])
        self.assertIsNotNone(config)

    def test_load_config_valid(self):
        config = load_config_file([os.path.abspath("tests/configs/full_valid.yaml")])
        self.assertIsNotNone(config)

    def test_load_config_valid_case_sensitivity(self):
        opsdroid, loader = self.setup()
        config = load_config_file(
            [os.path.abspath("tests/configs/valid_case_sensitivity.yaml")]
        )
        self.assertIsNotNone(config)

    def test_load_config_broken(self):

        with self.assertRaises(SystemExit) as cm:
            _ = load_config_file([os.path.abspath("tests/configs/full_broken.yaml")])
        self.assertEqual(cm.exception.code, 1)

    def test_load_config_file_2(self):
        config = load_config_file([os.path.abspath("tests/configs/minimal_2.yaml")])
        self.assertIsNotNone(config)

    def test_load_config_file_with_env_vars(self):
        os.environ["ENVVAR"] = "opsdroid"
        config = load_config_file(
            [os.path.abspath("tests/configs/minimal_with_envs.yaml")]
        )
        assert config["connectors"]["shell"]["bot-name"] == os.environ["ENVVAR"]

        config = load_config_file(
            [os.path.abspath("tests/configs/minimal_with_envs.json")]
        )
        assert config["connectors"]["shell"]["bot-name"] == os.environ["ENVVAR"]

    def test_create_default_config(self):
        test_config_path = os.path.join(
            tempfile.gettempdir(), "test_config_path/configuration.yaml"
        )

        self.assertEqual(create_default_config(test_config_path), test_config_path)
        self.assertTrue(os.path.isfile(test_config_path))
        shutil.rmtree(os.path.split(test_config_path)[0], onerror=del_rw)

    def test_generate_config_if_none_exist(self):
        # cdf_backup = create_default_config("tests/configs/minimal.yaml")
        with mock.patch(
            "opsdroid.configuration.create_default_config"
        ) as mocked_create_config:
            mocked_create_config.return_value = os.path.abspath(
                "tests/configs/minimal.yaml"
            )
            load_config_file(["file_which_does_not_exist"])
            self.assertTrue(mocked_create_config.called)

    def test_load_non_existant_config_file(self):
        with mock.patch("sys.exit") as mock_sysexit, mock.patch(
            "opsdroid.configuration.create_default_config"
        ) as mocked_create_default_config:
            mocked_create_default_config.return_value = os.path.abspath(
                "/tmp/my_nonexistant_config"
            )
            load_config_file(["file_which_does_not_exist"])
            self.assertTrue(mocked_create_default_config.called)
            self.assertLogs("_LOGGER", "critical")
            self.assertTrue(mock_sysexit.called)

    def test_load_broken_config_file(self):
        with mock.patch("sys.exit") as patched_sysexit:
            load_config_file([os.path.abspath("tests/configs/broken.yaml")])
            self.assertTrue(patched_sysexit.called)

    def test_load_bad_config_broken(self):
        with mock.patch("sys.exit") as mock_sysexit, mock.patch(
            "opsdroid.configuration.validate_data_type"
        ) as mocked_func:
            mocked_func.side_effect = TypeError()
            load_config_file(["file_which_does_not_exist"])
            self.assertTrue(mocked_func.called)
            self.assertLogs("_LOGGER", "critical")
            self.assertTrue(mock_sysexit.called)

    def test_validate_data_type(self):
        with self.assertRaises(TypeError):
            validate_data_type("bad config type")
