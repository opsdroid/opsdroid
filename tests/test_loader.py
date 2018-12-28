
import os
import shutil
import subprocess
import tempfile
import contextlib
import unittest
import unittest.mock as mock
from types import ModuleType

import pkg_resources
from opsdroid.__main__ import configure_lang
from opsdroid import loader as ld
from opsdroid.loader import Loader
from opsdroid.helper import del_rw


class TestLoader(unittest.TestCase):
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

    def test_yaml_load_exploit(self):
        with mock.patch('sys.exit'):
            config = Loader.load_config_file(
                [os.path.abspath("tests/configs/include_exploit.yaml")])
            self.assertIsNone(config)
            # If the command in exploit.yaml is echoed it will return 0
            self.assertNotEqual(config, 0)

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
        cdf_backup = Loader.create_default_config
        Loader.create_default_config = mock.Mock(
            return_value=os.path.abspath("tests/configs/minimal.yaml"))
        Loader.load_config_file(["file_which_does_not_exist"])
        self.assertTrue(Loader.create_default_config.called)
        Loader.create_default_config = cdf_backup

    def test_load_non_existant_config_file(self):
        cdf_backup = Loader.create_default_config
        Loader.create_default_config = mock.Mock(
            return_value=os.path.abspath("/tmp/my_nonexistant_config"))
        with mock.patch('sys.exit') as mock_sysexit:
            Loader.load_config_file(["file_which_does_not_exist"])
            self.assertTrue(Loader.create_default_config.called)
            self.assertTrue(mock_sysexit.called)
        Loader.create_default_config = cdf_backup

    def test_load_broken_config_file(self):
        with mock.patch('sys.exit') as patched_sysexit:
            Loader.load_config_file(
                [os.path.abspath("tests/configs/broken.yaml")])
            self.assertTrue(patched_sysexit.called)

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
        config = {"type": "test",
                  "name": "test",
                  "is_builtin": False}
        loader = mock.Mock()
        loader.modules_directory = ""
        self.assertIn("test.test",
                      ld.Loader.build_module_import_path(config))
        self.assertIn("test",
                      ld.Loader.build_module_install_path(loader, config))

        config["is_builtin"] = True
        self.assertIn("opsdroid.test.test",
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

    def test_no_dep(self):
        opsdroid, loader = self.setup()

        config = {}
        config['no-dep'] = True

        loader._install_module_dependencies(config)
        self.assertLogs('_LOGGER', 'debug')
        self.assertEqual(loader._install_module_dependencies(config), None)

        with mock.patch.object(loader, '_install_module_dependencies') \
                as nodep:
            config['no-dep'] = False
            self.assertTrue(nodep)

    def test_no_req_in_install_module_dependencies(self):
        opsdroid, loader = self.setup()
        config = {}
        config['install_path'] = ''

        with mock.patch('os.path.isfile') as file:
            file.return_value = False
            self.assertEqual(loader._install_module_dependencies(config), None)

    def test_import_module(self):
        config = {}
        config["module_path"] = "os"
        config["name"] = "path"
        config["type"] = "system"
        config["module"] = ""

        module = ld.Loader.import_module(config)
        self.assertIsInstance(module, ModuleType)

    def test_import_module_new(self):
        config = {}
        config["module_path"] = "os"
        config["name"] = ""
        config["type"] = "system"
        config["module"] = ""

        module = ld.Loader.import_module(config)
        self.assertIsInstance(module, ModuleType)

    def test_import_module_failure(self):
        config = {}
        config["module_path"] = "nonexistant"
        config["name"] = "module"
        config["type"] = "broken"
        config["module"] = ""

        module = ld.Loader.import_module(config)
        self.assertEqual(module, None)

    def test_import_module_from_path(self):
        config = {}
        config["module_path"] = ""
        config["name"] = "module"
        config["type"] = ""
        config["module"] = "os.path"

        module = ld.Loader.import_module(config)
        self.assertIsInstance(module, ModuleType)

    def test_import_module_from_entrypoint(self):

        config = {}
        config["module_path"] = ""
        config["name"] = "myep"
        config["type"] = ""
        config["module"] = ""

        distro = pkg_resources.Distribution()
        ep = pkg_resources.EntryPoint("myep", "os.path", dist=distro)
        config["entrypoint"] = ep

        opsdroid, loader = self.setup()
        loader.modules_directory = "."
        modules = [{"name": "myep"}]

        with mock.patch("opsdroid.loader.iter_entry_points") as mock_iter_entry_points:
            mock_iter_entry_points.return_value = (ep,)
            loaded = loader._load_modules("database", modules)
            self.assertEqual(loaded[0]["config"]["name"], "myep")

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
        self.assertEqual(len(loader._load_modules.mock_calls), 3)

    def test_load_empty_config(self):
        opsdroid, loader = self.setup()
        loader._load_modules = mock.MagicMock()
        config = {}

        loader.load_modules_from_config(config)
        self.assertEqual(len(loader._load_modules.mock_calls), 0)
        self.assertEqual(len(opsdroid.mock_calls), 2)

    def test_load_minimal_config_file(self):
        opsdroid, loader = self.setup()
        config = Loader.load_config_file(
            [os.path.abspath("tests/configs/minimal.yaml")])
        loader._install_module = mock.MagicMock()
        loader.import_module = mock.MagicMock()
        modules = loader.load_modules_from_config(config)
        self.assertIsNotNone(modules["connectors"])
        self.assertIsNone(modules["databases"])
        self.assertIsNotNone(modules["skills"])
        self.assertIsNotNone(config)

    def test_load_minimal_config_file_2(self):
        opsdroid, loader = self.setup()
        loader._install_module = mock.MagicMock()
        loader.import_module = mock.MagicMock()
        config = Loader.load_config_file(
            [os.path.abspath("tests/configs/minimal_2.yaml")])
        modules = loader.load_modules_from_config(config)
        self.assertIsNotNone(modules["connectors"])
        self.assertIsNone(modules["databases"])
        self.assertIsNotNone(modules["skills"])
        self.assertIsNotNone(config)

    def test_load_modules(self):
        opsdroid, loader = self.setup()

        modules_type = "test"
        modules = [{"name": "testmodule"}]
        mockedmodule = mock.Mock(return_value={"name": "testmodule"})

        with tempfile.TemporaryDirectory() as tmp_dep_path:
            with mock.patch.object(loader,
                                   '_install_module') as mockinstall, \
                    mock.patch('opsdroid.loader.DEFAULT_MODULE_DEPS_PATH',
                               os.path.join(tmp_dep_path,
                                            'site-packages')), \
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

    def test_install_gist_module(self):
        opsdroid, loader = self.setup()
        config = {"name": "ping",
                  "type": "skill",
                  "install_path": os.path.join(
                      self._tmp_dir, "test_gist_module_file"),
                  "gist": "https://gist.github.com/jacobtomlinson/"
                          "c9852fa17d3463acc14dca1217d911f6"}

        with mock.patch.object(loader, '_install_gist_module') as mockgist:
            loader._install_module(config)
            self.assertTrue(mockgist.called)

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
        with mock.patch.object(loader, 'pip_install_deps') as mockdeps:
            loader._install_module(config)
            self.assertLogs('_LOGGER', 'debug')
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

    def test_install_local_module_notebook(self):
        opsdroid, loader = self.setup()
        config = {"name": "slack",
                  "type": "connector",
                  "install_path": os.path.join(
                      self._tmp_dir, "test_local_module_file"),
                  "path": os.path.abspath(
                      "tests/mockmodules/skills/test_notebook.ipynb")}
        directory, _ = os.path.split(config["path"])
        os.makedirs(directory, exist_ok=True, mode=0o777)
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
        loader._install_local_module(config)
        self.assertLogs('_LOGGER', 'error')

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

        loader._update_module(config)
        self.assertLogs('_LOGGER', 'debug')

        shutil.rmtree(base_path, onerror=del_rw)

    def test_update_existing_git_module(self):
        opsdroid, loader = self.setup()
        config = {"name": "testmodule",
                  "install_path":
                  os.path.join(self._tmp_dir, "test_specific_remote_module"),
                  "repo": "https://github.com/rmccue/test-repository.git",
                  "branch": "master"}
        os.mkdir(config["install_path"])
        with mock.patch.object(loader, 'git_pull') as mockpull:
            loader._update_module(config)
            mockpull.assert_called_with(config["install_path"])

        shutil.rmtree(config["install_path"], onerror=del_rw)

    def test_install_gist_module_file(self):
        opsdroid, loader = self.setup()
        config = {"name": "ping",
                  "type": "skill",
                  "install_path": os.path.join(
                      self._tmp_dir, "test_gist_module_file"),
                  "gist": "https://gist.github.com/jacobtomlinson/"
                          "6dd35e0f62d6b779d3d0d140f338d3e5"}
        with mock.patch('urllib.request.urlopen') as mock_urlopen:
            with open(os.path.abspath(
                    'tests/responses/gist_module_file.json'), 'rb') as fh:
                mock_urlopen.return_value = fh
                loader._install_gist_module(config)
                self.assertTrue(os.path.isfile(os.path.join(
                    config["install_path"], "__init__.py")))
                shutil.rmtree(config["install_path"], onerror=del_rw)

    def test_install_gist_module_notebook(self):
        opsdroid, loader = self.setup()
        config = {"name": "ping",
                  "type": "skill",
                  "install_path": os.path.join(
                      self._tmp_dir, "test_gist_module_file"),
                  "gist": "https://gist.github.com/jacobtomlinson/"
                          "c9852fa17d3463acc14dca1217d911f6"}
        with mock.patch('urllib.request.urlopen') as mock_urlopen:
            with open(os.path.abspath(
                    'tests/responses/gist_module_notebook.json'), 'rb') as fh:
                mock_urlopen.return_value = fh
                loader._install_gist_module(config)
                self.assertTrue(os.path.isfile(os.path.join(
                    config["install_path"], "__init__.py")))
                shutil.rmtree(config["install_path"], onerror=del_rw)
