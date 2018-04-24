
import os
import tempfile
import unittest
import unittest.mock as mock

from opsdroid.helper import del_rw, move_config_to_appdir


class TestHelper(unittest.TestCase):
    """Test the opsdroid helper classes."""

    def test_del_rw(self):
        with mock.patch('os.chmod') as mock_chmod,\
                mock.patch('os.remove') as mock_remove:
            del_rw(None, None, None)
            self.assertTrue(mock_chmod.called)
            self.assertTrue(mock_remove.called)

    def test_move_config(self):
        with mock.patch('opsdroid.helper._LOGGER.info') as logmock, \
             mock.patch('os.remove') as mock_remove:
            move_config_to_appdir(
                os.path.abspath('tests/configs//'),
                tempfile.gettempdir())

            self.assertTrue(logmock.called)
            self.assertTrue(mock_remove.called)
