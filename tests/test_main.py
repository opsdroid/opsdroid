
import sys
import unittest
import unittest.mock as mock

import opsdroid.__main__ as opsdroid


class TestMain(unittest.TestCase):
    """Test the main opsdroid module."""

    def test_parse_args(self):
        args = opsdroid.parse_args(["--gen-config"])
        self.assertEqual(True, args.gen_config)

    # def test_gen_config(self):
    #     with mock.patch.object(sys, 'argv', ["--gen-config"]):
    #         with self.assertRaises(SystemExit) as sysexit:
    #             opsdroid.main()
    #         self.assertEqual(sysexit.exception.code, 0)

    # def test_check_version(self):
    #     with mock.patch.object(sys, 'version_info', [2, 2, 0]):
    #         self.assertEqual(sys.version_info[0], 2)
    #         with self.assertRaises(SystemExit) as sysexit:
    #             opsdroid.check_dependencies()
    #         self.assertEqual(sysexit.exception.code, 1)
