
import unittest
import unittest.mock as mock

from opsdroid.helper import del_rw


class TestHelper(unittest.TestCase):
    """Test the opsdroid helper classes."""

    def test_del_rw(self):
        with mock.patch('os.chmod') as mock_chmod,\
                mock.patch('os.remove') as mock_remove:
            del_rw(None, None, None)
            self.assertTrue(mock_chmod.called)
            self.assertTrue(mock_remove.called)
