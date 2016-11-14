
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

    def test_load_config_file(self):
        opsdroid, loader = self.setup()
        config = loader.load_config_file(["tests/configs/minimal.yaml"])
        self.assertIsNotNone(config)

    def test_load_non_existant_config_file(self):
        opsdroid, loader = self.setup()
        loader.opsdroid.critical = mock.Mock()
        loader.load_config_file(["file_which_does_not_exist"])
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
                             "/tmp/test", "master")
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
        self.assertIn("test.test",
                      ld.Loader.build_module_path("import", config))
        self.assertIn("test/test",
                      ld.Loader.build_module_path("install", config))

    def test_check_cache_removes(self):
        config = {}
        config["no-cache"] = True
        config['install_path'] = "/tmp/test/module"
        os.makedirs(config['install_path'])
        ld.Loader.check_cache(config)
        self.assertFalse(os.path.isdir(config["install_path"]))

    def test_check_cache_leaves(self):
        config = {}
        config["no-cache"] = False
        config['install_path'] = "/tmp/test/module"
        os.makedirs(config['install_path'])
        ld.Loader.check_cache(config)
        self.assertTrue(os.path.isdir(config["install_path"]))
        shutil.rmtree(config["install_path"])

    def test_import_module(self):
        config = {}
        config["path"] = "os"
        config["name"] = "path"
        config["type"] = "system"

        module = ld.Loader.import_module(config)
        self.assertIsInstance(module, ModuleType)

    def test_import_module_failure(self):
        config = {}
        config["path"] = "nonexistant"
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

        loader.load_config(config)
        self.assertEqual(len(loader._load_modules.mock_calls), 3)

    def test_load_empty_config(self):
        opsdroid, loader = self.setup()
        loader._load_modules = mock.MagicMock()
        config = {}

        loader.load_config(config)
        self.assertEqual(len(loader._load_modules.mock_calls), 0)
        self.assertEqual(len(opsdroid.mock_calls), 2)

    def test_load_modules(self):
        opsdroid, loader = self.setup()

        modules_type = "test"
        modules = {"testmodule": None}
        mockedmodule = mock.Mock(return_value={"name": "testmodule"})

        with mock.patch.object(loader, '_install_module') as mockinstall, \
                mock.patch.object(loader, 'import_module',
                                  mockedmodule) as mockimport:
            loader._load_modules(modules_type, modules)
            mockinstall.assert_called_with({
                'branch': 'master',
                'path': 'modules.test.testmodule',
                'name': 'testmodule',
                'type': modules_type,
                'install_path': 'modules/test/testmodule'})
            mockimport.assert_called_with({
                'path': 'modules.test.testmodule',
                'name': 'testmodule',
                'type': modules_type,
                'branch': 'master',
                'install_path':
                'modules/test/testmodule'})

    def test_install_existing_module(self):
        opsdroid, loader = self.setup()
        config = {"name": "testmodule",
                  "install_path": "/tmp/test_existing_module"}
        os.mkdir(config["install_path"])
        with mock.patch('logging.debug') as logmock:
            loader._install_module(config)
            logmock.assert_called_with(
                    'Module ' + config["name"] +
                    ' already installed, skipping')

    def test_install_missing_local_module(self):
        opsdroid, loader = self.setup()
        config = {"name": "testmodule",
                  "install_path": "/tmp/test_missing_local_module",
                  "repo": "/tmp/testrepo",
                  "branch": "master"}
        with mock.patch('logging.debug') as logmock:
            loader._install_module(config)
            logmock.assert_any_call(
                    "Could not find local git repo " + config["repo"])
            logmock.assert_any_call(
                    "Install of " + config["name"] + " failed")

    def test_install_specific_remote_module(self):
        opsdroid, loader = self.setup()
        config = {"name": "testmodule",
                  "install_path": "/tmp/test_specific_remote_module",
                  "repo": "https://github.com/rmccue/test-repository.git",
                  "branch": "master"}
        with mock.patch('logging.debug'), \
                mock.patch.object(loader, 'git_clone') as mockclone:
            loader._install_module(config)
            mockclone.assert_called_with(config["repo"],
                                         config["install_path"],
                                         config["branch"])

    def test_install_specific_local_module(self):
        opsdroid, loader = self.setup()
        config = {"name": "testmodule",
                  "install_path": "/tmp/testrepo",
                  "repo": "https://github.com/rmccue/test-repository.git",
                  "branch": "master"}
        loader._install_module(config)  # Clone remote repo for testing with
        config["repo"] = config["install_path"]
        config["install_path"] = "/tmp/test_specific_local_module"
        with mock.patch('logging.debug'), \
                mock.patch.object(loader, 'git_clone') as mockclone:
            loader._install_module(config)
            mockclone.assert_called_with(config["repo"],
                                         config["install_path"],
                                         config["branch"])

    def test_install_default_remote_module(self):
        opsdroid, loader = self.setup()
        config = {"name": "slack",
                  "type": "connector",
                  "install_path": "/tmp/test_default_remote_module",
                  "branch": "master"}
        with mock.patch('logging.debug') as logmock, \
                mock.patch.object(loader, 'pip_install_deps') as mockdeps:
            loader._install_module(config)
            logmock.assert_called_with(
                    'Installed ' + config["name"] +
                    ' to ' + config["install_path"])
            mockdeps.assert_called_with(
                    config["install_path"] + "/requirements.txt")
