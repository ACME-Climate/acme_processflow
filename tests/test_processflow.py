import unittest
import os
import sys
import shutil
import inspect

if sys.path[0] != '.':
    sys.path.insert(0, os.path.abspath('.'))

from configobj import ConfigObj
from lib.util import print_message
from processflow import main


class TestProcessflow(unittest.TestCase):

    def test_processflow_with_inplace_data(self):
        """
        End to end test of the processflow with inplace data
        """
        print('\n'); print_message('---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        config_path = os.path.join(
            os.getcwd(),
            'tests',
            'test_configs',
            'test_amwg_complete.cfg')

        config = ConfigObj(config_path)
        testargs = ['-c', config_path, '-r', 'resources', '--dryrun']
        ret = main(test=True, testargs=testargs)
        self.assertEqual(ret, 0)


if __name__ == '__main__':
    unittest.main()
