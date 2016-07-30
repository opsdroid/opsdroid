
import yaml
import unittest
import unittest.mock as mock

from opsdroid.loader import Loader  # noqa: E402


class TestLoader(unittest.TestCase):
    """Test the opsdroid loader class."""

    def setup(self):
        opsdroid = mock.MagicMock()
        loader = Loader(opsdroid)
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
