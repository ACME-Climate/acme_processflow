import unittest
import os, sys
import inspect

from configobj import ConfigObj
from threading import Event, Lock

if sys.path[0] != '.':
    sys.path.insert(0, os.path.abspath('.'))

from lib.events import EventList
from lib.jobstatus import JobStatus
from lib.util import print_message
from lib.filemanager import FileManager
from lib.runmanager import RunManager
from lib.initialize import initialize
from jobs.e3smdiags import E3SMDiags
from jobs.diag import Diag

class TestE3SM(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestE3SM, self).__init__(*args, **kwargs)
        self.event_list = EventList()
        self.config_path = 'tests/test_configs/e3sm_diags_complete.cfg'
        self.config = ConfigObj(self.config_path)

    def test_e3sm_diags_skip_complete(self):
        """
        Checks that the e3sm_diags job successfully marks a job thats already
        been run as complete and wont get executed
        """
        print('\n'); print_message('---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')

        e3sm_diags = E3SMDiags(
            short_name='piControl_testing',
            case='20180129.DECKv1b_piControl.ne30_oEC.edison',
            start=1,
            end=2,
            comparison='obs',
            config=self.config)
        
        self.assertTrue(isinstance(e3sm_diags, Diag))
        self.assertTrue(
            e3sm_diags.postvalidate(
                self.config,
                self.event_list))
    
    def test_e3sm_diags_prevalidate(self):
        """
        test that the e3sm_diags prevalidate and prerun setup works correctly
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
        
        self.assertFalse(config is None)
        self.assertFalse(filemanager is None)
        self.assertFalse(runmanager is None)

        config['global']['dryrun'] = True

        runmanager.check_data_ready()
        runmanager.start_ready_jobs()

        for case in runmanager.cases:
            for job in case['jobs']:
                if job.job_type == 'e3sm_diags':
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
