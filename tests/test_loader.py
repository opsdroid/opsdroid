
import yaml
import sys
import os
import shutil
from types import ModuleType
import unittest
import unittest.mock as mock

sys.modules['subprocess'] = mock.MagicMock()

from opsdroid import loader as ld  # noqa: E402


class TestLoader(unittest.TestCase):
    """Test the opsdroid loader class."""

    def setup(self):
        opsdroid = mock.MagicMock()
        loader = ld.Loader(opsdroid)
        return opsdroid, loader

    def test_load_config_file(self):
        opsdroid, loader = self.setup()
        config = loader.load_config_file("tests/configs/minimal.yaml")
        self.assertIsNotNone(config)

    def test_load_non_existant_config_file(self):
        opsdroid, loader = self.setup()
        loader.load_config_file("file_which_does_not_exist")
        self.assertEqual(len(opsdroid.mock_calls), 2)

    def test_load_broken_config_file(self):
        opsdroid, loader = self.setup()
        loader.load_config_file("tests/configs/broken.yaml")
        self.assertRaises(yaml.YAMLError)

    def test_setup_modules(self):
        opsdroid, loader = self.setup()
        example_modules = []
        example_modules.append({"module": mock.MagicMock()})
        loader._setup_modules(example_modules)
        self.assertEqual(len(example_modules[0]["module"].mock_calls), 1)

    def test_git_clone(self):
        ld.git_clone("https://github.com/rmccue/test-repository.git",
                     "/tmp/test", "master")
        self.assertNotEqual(len(sys.modules['subprocess'].mock_calls), 0)

    def test_build_module_path(self):
        config = {}
        config["type"] = "test"
        config["name"] = "test"
        self.assertIn("test.test", ld.build_module_path("import", config))
        self.assertIn("test/test", ld.build_module_path("install", config))

    def test_check_cache_removes(self):
        config = {}
        config["no-cache"] = True
        config['install_path'] = "/tmp/test/module"
        os.makedirs(config['install_path'])
        ld.check_cache(config)
        self.assertFalse(os.path.isdir(config["install_path"]))

    def test_check_cache_leaves(self):
        config = {}
        config["no-cache"] = False
        config['install_path'] = "/tmp/test/module"
        os.makedirs(config['install_path'])
        ld.check_cache(config)
        self.assertTrue(os.path.isdir(config["install_path"]))
        shutil.rmtree(config["install_path"])

    def test_import_module(self):
        config = {}
        config["path"] = "os"
        config["name"] = "path"
        config["type"] = "system"

        module = ld.import_module(config)
        self.assertIsInstance(module, ModuleType)

    def test_import_module_failure(self):
        config = {}
        config["path"] = "nonexistant"
        config["name"] = "module"
        config["type"] = "broken"

        module = ld.import_module(config)
        self.assertEqual(module, None)

    def test_load_config(self):
        opsdroid, loader = self.setup()
        loader._load_modules = mock.MagicMock()
        loader._setup_modules = mock.MagicMock()
        config = {}
        config['databases'] = mock.MagicMock()
        config['skills'] = mock.MagicMock()
        config['connectors'] = mock.MagicMock()

        loader.load_config(config)
        self.assertEqual(len(loader._load_modules.mock_calls), 3)
        self.assertEqual(len(loader._setup_modules.mock_calls), 1)
        self.assertEqual(len(opsdroid.mock_calls), 1)

    def test_load_empty_config(self):
        opsdroid, loader = self.setup()
        loader._load_modules = mock.MagicMock()
        loader._setup_modules = mock.MagicMock()
        config = {}

        loader.load_config(config)
        self.assertEqual(len(loader._load_modules.mock_calls), 0)
        self.assertEqual(len(loader._setup_modules.mock_calls), 0)
        self.assertEqual(len(opsdroid.mock_calls), 2)
