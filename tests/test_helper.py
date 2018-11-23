
import os
import tempfile
import unittest
import unittest.mock as mock

from opsdroid.helper import (
    del_rw, move_config_to_appdir, file_is_ipython_notebook,
    convert_ipynb_to_script, extract_gist_id)


class TestHelper(unittest.TestCase):
    """Test the opsdroid helper classes."""

    def test_del_rw(self):
        with mock.patch('os.chmod') as mock_chmod,\
                mock.patch('os.remove') as mock_remove:
            del_rw(None, None, None)
            self.assertTrue(mock_chmod.called)
            self.assertTrue(mock_remove.called)

    def test_move_config(self):
        with mock.patch('os.mkdir') as mock_mkdir, \
             mock.patch('os.path.isdir') as mock_isdir, \
             mock.patch('os.remove') as mock_remove:

            mock_isdir.return_value = False

            move_config_to_appdir(
                os.path.abspath('tests/configs/'),
                tempfile.gettempdir())

            self.assertTrue(mock_mkdir.called)
            self.assertLogs('_LOGGER', 'info')
            self.assertTrue(mock_remove.called)

    def test_file_is_ipython_notebook(self):
        self.assertTrue(file_is_ipython_notebook('test.ipynb'))
        self.assertFalse(file_is_ipython_notebook('test.py'))

    def test_convert_ipynb_to_script(self):
        notebook_path = \
            os.path.abspath("tests/mockmodules/skills/test_notebook.ipynb")

        with tempfile.NamedTemporaryFile(
                mode='w', delete=False) as output_file:
            convert_ipynb_to_script(notebook_path, output_file.name)
            self.assertTrue(os.path.getsize(output_file.name) > 0)

    def test_extract_gist_id(self):
        self.assertEqual(
            extract_gist_id(
                "https://gist.github.com/jacobtomlinson/"
                "c9852fa17d3463acc14dca1217d911f6"),
            "c9852fa17d3463acc14dca1217d911f6")

        self.assertEqual(
            extract_gist_id("c9852fa17d3463acc14dca1217d911f6"),
            "c9852fa17d3463acc14dca1217d911f6")
