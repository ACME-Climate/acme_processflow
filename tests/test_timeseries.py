import os
import sys
import unittest
import inspect
from configobj import ConfigObj

if sys.path[0] != '.':
    sys.path.insert(0, os.path.abspath('.'))

from jobs.Timeseries import Timeseries
from jobs.JobStatus import JobStatus
from lib.events import EventList
from lib.util import print_message

class TestTimeseries(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestTimeseries, self).__init__(*args, **kwargs)
        config_path = os.path.join(
            os.getcwd(), 'tests', 'test_configs', 'test_run_no_sta.cfg')
        self.config = ConfigObj(config_path)
        self.project_path = os.path.join(os.getcwd(), '..', 'testproject')

    def test_timeseries_setup(self):
        """
        test a valid timeseries setup
        """
        print('\n'); print_message('---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        timeseries = Timeseries({
            'regrid_output_directory': os.getcwd(),
            'filemanager': None,
            'year_set': 1,
            'annual_mode': 'sdd',
            'start_year': 50,
            'end_year': 55,
            'output_directory': os.path.join(self.project_path, 'output', 'monthly'),
            'var_list': self.config['ncclimo']['var_list'],
            'caseId': self.config['global']['experiment'],
            'run_scripts_path': os.path.join(self.project_path, 'output', 'run_scripts'),
            'regrid_map_path': self.config['ncclimo']['regrid_map_path'],
            'file_list': [],
        }, EventList())
        self.assertEqual(timeseries.status.name, 'VALID')


if __name__ == '__main__':
    unittest.main()
