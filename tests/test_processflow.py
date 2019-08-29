import inspect
import os
import sys
import unittest

from configobj import ConfigObj

from processflow.lib.util import print_message
from processflow.__main__ import main


class TestProcessflow(unittest.TestCase):

    def test_processflow_with_inplace_data(self):
        """
        End to end test of the processflow with inplace data
        """
        print '\n'; print_message('---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        config_path = os.path.join(
            os.getcwd(),
            'tests',
            'test_configs',
            'test_amwg_complete.cfg')

        config = ConfigObj(config_path)
        testargs = ['--test', '-c', config_path, '-r', 'resources', '--dryrun']
        ret = main(testargs)
        self.assertEqual(ret, 0)


if __name__ == '__main__':
    unittest.main()
