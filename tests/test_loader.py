
import os
import shutil
from types import ModuleType
import unittest
import unittest.mock as mock
import subprocess

from opsdroid import loader as ld


class TestLoader(unittest.TestCase):
    """Test the opsdroid loader class."""

    def setup(self):
        opsdroid = mock.MagicMock()
        loader = ld.Loader(opsdroid)
        return opsdroid, loader

    def setUp(self):
        self._tmp_dir = "/tmp/opsdroid_tests"
        os.makedirs(self._tmp_dir)

    def tearDown(self):
        shutil.rmtree(self._tmp_dir)

    def test_load_config_file(self):
        opsdroid, loader = self.setup()
        config = loader.load_config_file(["tests/configs/minimal.yaml"])
        self.assertIsNotNone(config)

    def test_load_config_file_2(self):
        opsdroid, loader = self.setup()
        config = loader.load_config_file(["tests/configs/minimal_2.yaml"])
        self.assertIsNotNone(config)

    def test_load_config_file_with_include(self):
        opsdroid, loader = self.setup()
        config = loader.load_config_file(
                                ["tests/configs/minimal_with_include.yaml"])
        config2 = loader.load_config_file(["tests/configs/minimal.yaml"])
        self.assertIsNotNone(config)
        self.assertEqual(config, config2)

    def test_load_config_file_with_env_vars(self):
        opsdroid, loader = self.setup()
        os.environ["ENVVAR"] = 'test'
        config = loader.load_config_file(
            ["tests/configs/minimal_with_envs.yaml"])
        self.assertEqual(config["test"], os.environ["ENVVAR"])

    def test_create_default_config(self):
        test_config_path = "/tmp/test_config_path/configuration.yaml"
        opsdroid, loader = self.setup()

        self.assertEqual(loader.create_default_config(test_config_path),
                         test_config_path)
        self.assertTrue(os.path.isfile(test_config_path))
        shutil.rmtree(os.path.split(test_config_path)[0])

    def test_generate_config_if_none_exist(self):
        opsdroid, loader = self.setup()
        loader.create_default_config = mock.Mock(
            return_value="tests/configs/minimal.yaml")
        loader.load_config_file(["file_which_does_not_exist"])
        self.assertTrue(loader.create_default_config.called)

    def test_load_non_existant_config_file(self):
        opsdroid, loader = self.setup()
        loader.create_default_config = mock.Mock(
            return_value="/tmp/my_nonexistant_config")
        loader.load_config_file(["file_which_does_not_exist"])
        self.assertTrue(loader.create_default_config.called)
        self.assertTrue(loader.opsdroid.critical.called)

    def test_load_broken_config_file(self):
        opsdroid, loader = self.setup()
        loader.opsdroid.critical = mock.Mock()
        loader.load_config_file(["tests/configs/broken.yaml"])
        self.assertTrue(loader.opsdroid.critical.called)

    def test_git_clone(self):
        with mock.patch.object(subprocess, 'Popen') as mock_subproc_popen:
            opsdroid, loader = self.setup()
            loader.git_clone("https://github.com/rmccue/test-repository.git",
                             self._tmp_dir + "/test", "master")
            self.assertTrue(mock_subproc_popen.called)

    def test_pip_install_deps(self):
        with mock.patch.object(subprocess, 'Popen') as mocked_popen:
            mocked_popen.return_value.communicate.return_value = ['Test\nTest']
            opsdroid, loader = self.setup()
            loader.pip_install_deps("/path/to/some/file.txt")
            self.assertTrue(mocked_popen.called)

    def test_build_module_path(self):
        config = {}
        config["type"] = "test"
        config["name"] = "test"
        loader = mock.Mock()
        loader.modules_directory = ""
        self.assertIn("test.test",
                      ld.Loader.build_module_path(loader, "import", config))
        self.assertIn("test/test",
                      ld.Loader.build_module_path(loader, "install", config))

    def test_check_cache_removes_dir(self):
        config = {}
        config["no-cache"] = True
        config['install_path'] = self._tmp_dir + "/test/module"
        os.makedirs(config['install_path'])
        ld.Loader.check_cache(config)
        self.assertFalse(os.path.isdir(config["install_path"]))

    def test_check_cache_removes_file(self):
        config = {}
        config["no-cache"] = True
        config['install_path'] = self._tmp_dir + "/test/module/test"
        directory, _ = os.path.split(config['install_path'])
        os.makedirs(directory)
        open(config['install_path'] + ".py", 'w')
        ld.Loader.check_cache(config)
        self.assertFalse(os.path.isfile(config["install_path"] + ".py"))
        shutil.rmtree(directory)

    def test_check_cache_leaves(self):
        config = {}
        config["no-cache"] = False
        config['install_path'] = self._tmp_dir + "/test/module"
        os.makedirs(config['install_path'])
        ld.Loader.check_cache(config)
        self.assertTrue(os.path.isdir(config["install_path"]))
        shutil.rmtree(config["install_path"])

    def test_import_module(self):
        config = {}
        config["module_path"] = "os"
        config["name"] = "path"
        config["type"] = "system"

        module = ld.Loader.import_module(config)
        self.assertIsInstance(module, ModuleType)

    def test_import_module_new(self):
        config = {}
        config["module_path"] = "os"
        config["name"] = ""
        config["type"] = "system"

        module = ld.Loader.import_module(config)
        self.assertIsInstance(module, ModuleType)

    def test_import_module_failure(self):
        config = {}
        config["module_path"] = "nonexistant"
        config["name"] = "module"
        config["type"] = "broken"

        module = ld.Loader.import_module(config)
        self.assertEqual(module, None)

    def test_load_config(self):
        opsdroid, loader = self.setup()
        loader._load_modules = mock.MagicMock()
        loader._setup_modules = mock.MagicMock()
        config = {}
        config['databases'] = mock.MagicMock()
        config['skills'] = mock.MagicMock()
        config['connectors'] = mock.MagicMock()
        config['module-path'] = self._tmp_dir + "/opsdroid"

        loader.load_modules_from_config(config)
        self.assertEqual(len(loader._load_modules.mock_calls), 4)

    def test_load_empty_config(self):
        opsdroid, loader = self.setup()
        loader._load_modules = mock.MagicMock()
        config = {}

        loader.load_modules_from_config(config)
        self.assertEqual(len(loader._load_modules.mock_calls), 0)
        self.assertEqual(len(opsdroid.mock_calls), 2)

    def test_load_minimal_config_file(self):
        opsdroid, loader = self.setup()
        config = loader.load_config_file(["tests/configs/minimal.yaml"])
        loader._install_module = mock.MagicMock()
        loader.import_module = mock.MagicMock()
        loader._reload_modules = mock.MagicMock()
        connectors, databases, skills = loader.load_modules_from_config(config)
        self.assertIsNotNone(connectors)
        self.assertIsNone(databases)
        self.assertIsNotNone(skills)
        self.assertIsNotNone(config)

    def test_load_minimal_config_file_2(self):
        opsdroid, loader = self.setup()
        loader._install_module = mock.MagicMock()
        loader.import_module = mock.MagicMock()
        loader._reload_modules = mock.MagicMock()
        config = loader.load_config_file(["tests/configs/minimal_2.yaml"])
        connectors, databases, skills = loader.load_modules_from_config(config)
        self.assertIsNotNone(config)
        self.assertIsNotNone(connectors)
        self.assertIsNone(databases)
        self.assertIsNotNone(skills)

    def test_load_modules(self):
        opsdroid, loader = self.setup()

        modules_type = "test"
        modules = [{"name": "testmodule"}]
        mockedmodule = mock.Mock(return_value={"name": "testmodule"})

        with mock.patch.object(loader, '_install_module') as mockinstall, \
                mock.patch.object(loader, 'import_module',
                                  mockedmodule) as mockimport:
            loader.setup_modules_directory({})
            loader._load_modules(modules_type, modules)
            self.assertTrue(mockinstall.called)
            self.assertTrue(mockimport.called)

    def test_load_modules_fail(self):
        opsdroid, loader = self.setup()

        modules_type = "test"
        modules = [{"name": "testmodule"}]

        with mock.patch.object(loader, '_install_module') as mockinstall, \
                mock.patch.object(loader, 'import_module',
                                  return_value=None) as mockimport:
            loader.setup_modules_directory({})
            loaded_modules = loader._load_modules(modules_type, modules)
            self.assertTrue(mockinstall.called)
            self.assertTrue(mockimport.called)
            self.assertEqual(loaded_modules, [])

    def test_install_existing_module(self):
        opsdroid, loader = self.setup()
        config = {"name": "testmodule",
                  "install_path": self._tmp_dir + "/test_existing_module"}
        os.mkdir(config["install_path"])
        with mock.patch('opsdroid.loader._LOGGER.debug') as logmock:
            loader._install_module(config)
            self.assertTrue(logmock.called)

        shutil.rmtree(config["install_path"])

    def test_install_missing_local_module(self):
        opsdroid, loader = self.setup()
        config = {"name": "testmodule",
                  "install_path": self._tmp_dir + "/test_missing_local_module",
                  "repo": self._tmp_dir + "/testrepo",
                  "branch": "master"}
        with mock.patch('opsdroid.loader._LOGGER.error') as logmock:
            loader._install_module(config)
            logmock.assert_any_call(
                    "Could not find local git repo %s", config["repo"])
            logmock.assert_any_call(
                    "Install of %s failed.", config["name"])

    def test_install_specific_remote_module(self):
        opsdroid, loader = self.setup()
        config = {"name": "testmodule",
                  "install_path":
                  self._tmp_dir + "/test_specific_remote_module",
                  "repo": "https://github.com/rmccue/test-repository.git",
                  "branch": "master"}
        with mock.patch('opsdroid.loader._LOGGER.debug'), \
                mock.patch.object(loader, 'git_clone') as mockclone:
            loader._install_module(config)
            mockclone.assert_called_with(config["repo"],
                                         config["install_path"],
                                         config["branch"])

    def test_install_specific_local_git_module(self):
        opsdroid, loader = self.setup()
        repo_path = self._tmp_dir + "/testrepo"
        config = {"name": "testmodule",
                  "install_path": repo_path,
                  "repo": "https://github.com/rmccue/test-repository.git",
                  "branch": "master"}
        loader._install_module(config)  # Clone remote repo for testing with
        config["repo"] = config["install_path"] + "/.git"
        config["install_path"] = self._tmp_dir + "/test_specific_local_module"
        with mock.patch('opsdroid.loader._LOGGER.debug'), \
                mock.patch.object(loader, 'git_clone') as mockclone:
            loader._install_module(config)
            mockclone.assert_called_with(config["repo"],
                                         config["install_path"],
                                         config["branch"])
        shutil.rmtree(repo_path)

    def test_install_specific_local_path_module(self):
        opsdroid, loader = self.setup()
        repo_path = self._tmp_dir + "/testrepo"
        config = {"name": "testmodule",
                  "install_path": repo_path,
                  "repo": "https://github.com/rmccue/test-repository.git",
                  "branch": "master"}
        loader._install_module(config)  # Clone remote repo for testing with
        config["path"] = config["install_path"]
        config["install_path"] = self._tmp_dir + "/test_specific_local_module"
        with mock.patch('opsdroid.loader._LOGGER.debug'), \
                mock.patch.object(loader, '_install_local_module') \
                as mockclone:
            loader._install_module(config)
            mockclone.assert_called_with(config)
        shutil.rmtree(repo_path)

    def test_install_default_remote_module(self):
        opsdroid, loader = self.setup()
        config = {"name": "slack",
                  "type": "connector",
                  "install_path":
                  self._tmp_dir + "/test_default_remote_module",
                  "branch": "master"}
        with mock.patch('opsdroid.loader._LOGGER.debug') as logmock, \
                mock.patch.object(loader, 'pip_install_deps') as mockdeps:
            loader._install_module(config)
            self.assertTrue(logmock.called)
            mockdeps.assert_called_with(
                    config["install_path"] + "/requirements.txt")

        shutil.rmtree(config["install_path"])

    def test_install_local_module_dir(self):
        opsdroid, loader = self.setup()
        base_path = self._tmp_dir + "/long"
        config = {"name": "slack",
                  "type": "connector",
                  "install_path": base_path + "/test/path/test",
                  "path": self._tmp_dir + "/install/from/here"}
        os.makedirs(config["path"], exist_ok=True)
        loader._install_local_module(config)
        self.assertTrue(os.path.isdir(config["install_path"]))
        shutil.rmtree(base_path)

    def test_install_local_module_file(self):
        opsdroid, loader = self.setup()
        config = {"name": "slack",
                  "type": "connector",
                  "install_path": self._tmp_dir + "/test_local_module_file",
                  "path": self._tmp_dir + "/install/from/here.py"}
        directory, _ = os.path.split(config["path"])
        os.makedirs(directory, exist_ok=True)
        open(config["path"], 'w')
        loader._install_local_module(config)
        self.assertTrue(os.path.isfile(
                            config["install_path"] + "/__init__.py"))
        shutil.rmtree(config["install_path"])

    def test_install_local_module_failure(self):
        opsdroid, loader = self.setup()
        config = {"name": "slack",
                  "type": "connector",
                  "install_path": self._tmp_dir + "/test_local_module_failure",
                  "path": self._tmp_dir + "/does/not/exist"}
        with mock.patch('opsdroid.loader._LOGGER.error') as logmock:
            loader._install_local_module(config)
            self.assertTrue(logmock.called)

    def test_reload_module(self):
        config = {}
        config["module_path"] = "os.path"
        config["name"] = "path"
        config["type"] = "system"
        from os import path
        opsdriod, loader = self.setup()
        with mock.patch('importlib.reload') as reload_mock:
            mock_module = {"module": path,
                           "config": config}
            loader._reload_modules([mock_module])
        self.assertTrue(reload_mock.called)

    def test_reload_module_fake_import(self):
        opsdroid, loader = self.setup()
        with mock.patch('importlib.reload') as reload_mock:
            mock_module = {"module": "fake_import",
                           "config": {}}
            loader._reload_modules([mock_module])
            self.assertTrue(reload_mock.called_with("fake_import"))
