import os, sys
import unittest
import shutil
import inspect

from configobj import ConfigObj
from threading import Event

if sys.path[0] != '.':
    sys.path.insert(0, os.path.abspath('.'))

from lib.events import EventList
from lib.jobstatus import JobStatus
from lib.util import print_message
from lib.filemanager import FileManager
from lib.runmanager import RunManager
from lib.initialize import initialize
from jobs.amwg import AMWG
from jobs.diag import Diag


class TestAMWGDiagnostic(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestAMWGDiagnostic, self).__init__(*args, **kwargs)
        self.config_path = os.path.join(
            os.getcwd(),
            'tests',
            'test_configs',
            'test_amwg_complete.cfg')
        self.config = ConfigObj(self.config_path)
        self.config['global']['run_scripts_path'] = os.path.join(
            self.config['global']['project_path'],
            'output',
            'scripts')
        self.event_list = EventList()

    def test_amwg_setup(self):
        """
        Test the amwg initialization and data setup works correctly
        """
        print('\n'); print_message('---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        _args = ['-c', self.config_path]
        config, filemanager, runmanager = initialize(
            argv=_args,
            version="2.0.0",
            branch="testing",
            event_list=self.event_list,
            kill_event=Event(),
            testing=True)
        
        amwg = AMWG(
            short_name='piControl_testing',
            case='20180129.DECKv1b_piControl.ne30_oEC.edison',
            start=1,
            end=2,
            comparison='obs',
            config=self.config)

        self.assertTrue(isinstance(amwg, Diag))

    def test_amwg_prevalidate(self):
        """
        test that the amwg execution (in dry run mode) words correctly
        """
        print('\n'); print_message('---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        _args = ['-c', self.config_path]
        config, filemanager, runmanager = initialize(
            argv=_args,
            version="2.0.0",
            branch="testing",
            event_list=self.event_list,
            kill_event=Event(),
            testing=True)
        
        self.assertFalse(config is None)
        self.assertFalse(filemanager is None)
        self.assertFalse(runmanager is None)

    def test_amwg_execution_completed_job(self):
        """
        test that when run on a completed set of jobs, amwg recognizes that the run has already
        taken place and doesnt start again
        """
        print('\n'); print_message('---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        _args = ['-c', self.config_path, '-r', 'resources/']
        config, filemanager, runmanager = initialize(
            argv=_args,
            version="2.0.0",
            branch="testing",
            event_list=self.event_list,
            kill_event=Event(),
            testing=True)

        config['global']['dryrun'] = True

        runmanager.check_data_ready()
        runmanager.start_ready_jobs()
        
        for case in runmanager.cases:
            for job in case['jobs']:
                if job.job_type == 'amwg':
                    job.setup_data(
                        config=config,
                        filemanager=filemanager,
                        case='20180129.DECKv1b_piControl.ne30_oEC.edison')
                    job.execute(
                        config=config,
                        dryrun=True)
                    self.assertEqual(
                        job.status,
                        JobStatus.COMPLETED)

if __name__ == '__main__':
    unittest.main()
