
import os
import shutil
import subprocess
import tempfile
import unittest
import unittest.mock as mock
from types import ModuleType

from opsdroid import loader as ld
from opsdroid.helper import del_rw


class TestLoader(unittest.TestCase):
    """Test the opsdroid loader class."""

    def setup(self):
        opsdroid = mock.MagicMock()
        loader = ld.Loader(opsdroid)
        return opsdroid, loader

    def setUp(self):
        os.umask(000)
        self._tmp_dir = os.path.join(tempfile.gettempdir(), "opsdroid_tests")
        try:
            os.makedirs(self._tmp_dir, mode=0o777)
        except FileExistsError:
            pass

    def tearDown(self):
        shutil.rmtree(self._tmp_dir, onerror=del_rw)

    def test_load_config_file(self):
        opsdroid, loader = self.setup()
        config = loader.load_config_file(
            [os.path.abspath("tests/configs/minimal.yaml")])
        self.assertIsNotNone(config)

    def test_load_config_file_2(self):
        opsdroid, loader = self.setup()
        config = loader.load_config_file(
            [os.path.abspath("tests/configs/minimal_2.yaml")])
        self.assertIsNotNone(config)

    def test_load_config_file_with_include(self):
        opsdroid, loader = self.setup()
        config = loader.load_config_file(
            [os.path.abspath("tests/configs/minimal_with_include.yaml")])
        config2 = loader.load_config_file(
            [os.path.abspath("tests/configs/minimal.yaml")])
        self.assertIsNotNone(config)
        self.assertEqual(config, config2)

    def test_load_config_file_with_env_vars(self):
        opsdroid, loader = self.setup()
        os.environ["ENVVAR"] = 'test'
        config = loader.load_config_file(
            [os.path.abspath("tests/configs/minimal_with_envs.yaml")])
        self.assertEqual(config["test"], os.environ["ENVVAR"])

    def test_create_default_config(self):
        test_config_path = os.path.join(
            tempfile.gettempdir(), "test_config_path/configuration.yaml")
        opsdroid, loader = self.setup()

        self.assertEqual(loader.create_default_config(test_config_path),
                         test_config_path)
        self.assertTrue(os.path.isfile(test_config_path))
        shutil.rmtree(os.path.split(test_config_path)[0], onerror=del_rw)

    def test_generate_config_if_none_exist(self):
        opsdroid, loader = self.setup()
        loader.create_default_config = mock.Mock(
            return_value=os.path.abspath("tests/configs/minimal.yaml"))
        loader.load_config_file(["file_which_does_not_exist"])
        self.assertTrue(loader.create_default_config.called)

    def test_load_non_existant_config_file(self):
        opsdroid, loader = self.setup()
        loader.create_default_config = mock.Mock(
            return_value=os.path.abspath("/tmp/my_nonexistant_config"))
        loader.load_config_file(["file_which_does_not_exist"])
        self.assertTrue(loader.create_default_config.called)
        self.assertTrue(loader.opsdroid.critical.called)

    def test_load_broken_config_file(self):
        opsdroid, loader = self.setup()
        loader.opsdroid.critical = mock.Mock()
        loader.load_config_file(
            [os.path.abspath("tests/configs/broken.yaml")])
        self.assertTrue(loader.opsdroid.critical.called)

    def test_git_clone(self):
        with mock.patch.object(subprocess, 'Popen') as mock_subproc_popen:
            opsdroid, loader = self.setup()
            loader.git_clone("https://github.com/rmccue/test-repository.git",
                             os.path.join(self._tmp_dir, "/test"), "master")
            self.assertTrue(mock_subproc_popen.called)

    def test_git_pull(self):
        with mock.patch.object(subprocess, 'Popen') as mock_subproc_popen:
            opsdroid, loader = self.setup()
            loader.git_pull(os.path.join(self._tmp_dir, "/test"))
            self.assertTrue(mock_subproc_popen.called)

    def test_pip_install_deps(self):
        with mock.patch.object(subprocess, 'Popen') as mocked_popen:
            mocked_popen.return_value.communicate.return_value = ['Test\nTest']
            opsdroid, loader = self.setup()
            loader.pip_install_deps(os.path.abspath("/path/to/some/file.txt"))
            self.assertTrue(mocked_popen.called)

    def test_no_pip_install(self):
        opsdroid, loader = self.setup()
        with mock.patch.object(loader, 'pip_install_deps') as mock_pip:
            mock_pip.side_effect = FileNotFoundError()
            with self.assertRaises(FileNotFoundError):
                mock_pip.return_value.communicate.return_value = ['Test\nTest']
                loader.pip_install_deps("/path/to/some/file.txt")
                self.assertTrue(mock_pip.called)

    def test_no_pip_or_pip3_install(self):
        opsdroid, loader = self.setup()
        loader.pip_install_deps("/path/to/some/file.txt")

        with mock.patch.object(subprocess, 'Popen') as mocked_popen:
            mocked_popen.side_effect = [
                FileNotFoundError(), FileNotFoundError()]
            with self.assertRaises(OSError) as error:
                loader.pip_install_deps("/path/to/some/file.txt")
                self.assertEqual(error, "Pip and pip3 not found, exiting...")

    def test_build_module_path(self):
        config = {}
        config["type"] = "test"
        config["name"] = "test"
        loader = mock.Mock()
        loader.modules_directory = ""
        self.assertIn("test.test",
                      ld.Loader.build_module_import_path(config))
        self.assertIn("test",
                      ld.Loader.build_module_install_path(loader, config))

    def test_check_cache_removes_dir(self):
        config = {}
        config["no-cache"] = True
        config['install_path'] = os.path.join(
            self._tmp_dir, os.path.normpath("test/module"))
        os.makedirs(config['install_path'], mode=0o777)
        ld.Loader.check_cache(config)
        self.assertFalse(os.path.isdir(config["install_path"]))

    def test_check_cache_removes_file(self):
        config = {}
        config["no-cache"] = True
        config['install_path'] = os.path.join(
            self._tmp_dir, os.path.normpath("test/module/test"))
        directory, _ = os.path.split(config['install_path'])
        os.makedirs(directory, mode=0o777)
        open(config['install_path'] + ".py", 'w')
        ld.Loader.check_cache(config)
        self.assertFalse(os.path.isfile(config["install_path"] + ".py"))
        shutil.rmtree(directory, onerror=del_rw)

    def test_check_cache_leaves(self):
        config = {}
        config["no-cache"] = False
        config['install_path'] = os.path.join(
            self._tmp_dir, os.path.normpath("test/module"))
        os.makedirs(config['install_path'], mode=0o777)
        ld.Loader.check_cache(config)
        self.assertTrue(os.path.isdir(config["install_path"]))
        shutil.rmtree(config["install_path"], onerror=del_rw)

    def test_loading_intents(self):
        config = {}
        config["no-cache"] = True
        config['install_path'] = os.path.join(
            self._tmp_dir, os.path.normpath("test/module/test"))
        os.makedirs(config['install_path'], mode=0o777)
        intent_contents = "Hello world"
        intents_file = os.path.join(config['install_path'], "intents.md")
        with open(intents_file, 'w') as intents:
            intents.write(intent_contents)
        loaded_intents = ld.Loader._load_intents(config)
        self.assertEqual(intent_contents, loaded_intents)
        shutil.rmtree(config["install_path"], onerror=del_rw)

    def test_loading_intents_failed(self):
        config = {}
        config["no-cache"] = True
        config['install_path'] = os.path.join(
            self._tmp_dir, os.path.normpath("test/module/test/"))
        loaded_intents = ld.Loader._load_intents(config)
        self.assertEqual(None, loaded_intents)

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
        config['module-path'] = os.path.join(self._tmp_dir, "opsdroid")

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
        config = loader.load_config_file(
            [os.path.abspath("tests/configs/minimal.yaml")])
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
        config = loader.load_config_file(
            [os.path.abspath("tests/configs/minimal_2.yaml")])
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

    def test_load_existing_modules(self):
        opsdroid, loader = self.setup()

        modules_type = "test"
        modules = [{"name": "testmodule"}]
        install_path = os.path.join(
            self._tmp_dir, "test_existing_module")
        mockedmodule = mock.Mock(return_value={"name": "testmodule"})
        mocked_install_path = mock.Mock(return_value=install_path)

        os.mkdir(install_path)
        with mock.patch.object(loader, '_update_module') as mockupdate, \
                mock.patch.object(loader, 'import_module',
                                  mockedmodule) as mockimport, \
                mock.patch.object(loader, 'build_module_install_path',
                                  mocked_install_path) as mockbuildpath:
            loader.setup_modules_directory({})
            loader._load_modules(modules_type, modules)
            self.assertTrue(mockbuildpath.called)
            self.assertTrue(mockupdate.called)
            self.assertTrue(mockimport.called)

        shutil.rmtree(install_path, onerror=del_rw)

    def test_install_missing_local_module(self):
        opsdroid, loader = self.setup()
        config = {"name": "testmodule",
                  "install_path": os.path.join(
                      self._tmp_dir, "test_missing_local_module"),
                  "repo": os.path.join(self._tmp_dir, "testrepo"),
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
                  os.path.join(self._tmp_dir, "test_specific_remote_module"),
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
        repo_path = os.path.join(self._tmp_dir, "testrepo")
        config = {"name": "testmodule",
                  "install_path": repo_path,
                  "repo": "https://github.com/rmccue/test-repository.git",
                  "branch": "master"}
        loader._install_module(config)  # Clone remote repo for testing with
        config["repo"] = os.path.join(config["install_path"], ".git")
        config["install_path"] = os.path.join(
            self._tmp_dir, "test_specific_local_module")
        with mock.patch('opsdroid.loader._LOGGER.debug'), \
                mock.patch.object(loader, 'git_clone') as mockclone:
            loader._install_module(config)
            mockclone.assert_called_with(config["repo"],
                                         config["install_path"],
                                         config["branch"])
        shutil.rmtree(repo_path, onerror=del_rw)

    def test_install_specific_local_path_module(self):
        opsdroid, loader = self.setup()
        repo_path = os.path.join(self._tmp_dir, "testrepo")
        config = {"name": "testmodule",
                  "install_path": repo_path,
                  "repo": "https://github.com/rmccue/test-repository.git",
                  "branch": "master"}
        loader._install_module(config)  # Clone remote repo for testing with
        config["path"] = config["install_path"]
        config["install_path"] = os.path.join(
            self._tmp_dir, "test_specific_local_module")
        with mock.patch('opsdroid.loader._LOGGER.debug'), \
                mock.patch.object(loader, '_install_local_module') \
                as mockclone:
            loader._install_module(config)
            mockclone.assert_called_with(config)
        shutil.rmtree(repo_path, onerror=del_rw)

    def test_install_default_remote_module(self):
        opsdroid, loader = self.setup()
        config = {"name": "slack",
                  "type": "connector",
                  "install_path":
                  os.path.join(self._tmp_dir, "test_default_remote_module"),
                  "branch": "master"}
        with mock.patch('opsdroid.loader._LOGGER.debug') as logmock, \
                mock.patch.object(loader, 'pip_install_deps') as mockdeps:
            loader._install_module(config)
            self.assertTrue(logmock.called)
            mockdeps.assert_called_with(
                    os.path.join(config["install_path"], "requirements.txt"))

        shutil.rmtree(config["install_path"], onerror=del_rw)

    def test_install_local_module_dir(self):
        opsdroid, loader = self.setup()
        base_path = os.path.join(self._tmp_dir, "long")
        config = {"name": "slack",
                  "type": "connector",
                  "install_path": os.path.join(
                      base_path, os.path.normpath("test/path/test")),
                  "path": os.path.join(
                      self._tmp_dir, os.path.normpath("install/from/here"))}
        os.makedirs(config["path"], exist_ok=True, mode=0o777)
        loader._install_local_module(config)
        self.assertTrue(os.path.isdir(config["install_path"]))
        shutil.rmtree(base_path, onerror=del_rw)

    def test_install_local_module_file(self):
        opsdroid, loader = self.setup()
        config = {"name": "slack",
                  "type": "connector",
                  "install_path": os.path.join(
                      self._tmp_dir, "test_local_module_file"),
                  "path": os.path.join(
                      self._tmp_dir, os.path.normpath("install/from/here.py"))}
        directory, _ = os.path.split(config["path"])
        os.makedirs(directory, exist_ok=True, mode=0o777)
        open(config["path"], 'w')
        loader._install_local_module(config)
        self.assertTrue(os.path.isfile(os.path.join(
            config["install_path"], "__init__.py")))
        shutil.rmtree(config["install_path"], onerror=del_rw)

    def test_install_local_module_failure(self):
        opsdroid, loader = self.setup()
        config = {"name": "slack",
                  "type": "connector",
                  "install_path": os.path.join(
                      self._tmp_dir, "test_local_module_failure"),
                  "path": os.path.join(self._tmp_dir, "doesnotexist")}
        with mock.patch('opsdroid.loader._LOGGER.error') as logmock:
            loader._install_local_module(config)
            self.assertTrue(logmock.called)

    def test_update_existing_local_module(self):
        opsdroid, loader = self.setup()
        base_path = os.path.join(self._tmp_dir, "long")
        config = {"name": "testmodule",
                  "type": "test",
                  "install_path": os.path.join(
                      base_path, os.path.normpath("test/path/test")),
                  "path": os.path.join(
                      self._tmp_dir, os.path.normpath("install/from/here"))}
        os.makedirs(config["install_path"], exist_ok=True, mode=0o777)
        os.makedirs(config["path"], exist_ok=True, mode=0o777)

        with mock.patch('opsdroid.loader._LOGGER.debug') as logmock:
            loader._update_module(config)
            self.assertTrue(logmock.called)

        shutil.rmtree(base_path, onerror=del_rw)

    def test_update_existing_git_module(self):
        opsdroid, loader = self.setup()
        config = {"name": "testmodule",
                  "install_path":
                  os.path.join(self._tmp_dir, "test_specific_remote_module"),
                  "repo": "https://github.com/rmccue/test-repository.git",
                  "branch": "master"}
        os.mkdir(config["install_path"])
        with mock.patch('opsdroid.loader._LOGGER.debug'), \
                mock.patch.object(loader, 'git_pull') as mockpull:
            loader._update_module(config)
            mockpull.assert_called_with(config["install_path"])

        shutil.rmtree(config["install_path"], onerror=del_rw)

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
