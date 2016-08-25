
import sys
import unittest
import unittest.mock as mock

sys.modules['sys'].exit = mock.MagicMock()

import opsdroid.__main__ as opsdroid  # noqa: E402


class TestMain(unittest.TestCase):
    """Test the main opsdroid module."""

    def test_parse_args(self):
        args = opsdroid.parse_args(["--gen-config"])
        self.assertEqual(True, args.gen_config)

    def text_gen_config(self):
        sys.argv = ["--gen-config"]
        opsdroid.main()
        self.assertEqual(1, len(sys.modules['sys'].exit.mock_calls))
