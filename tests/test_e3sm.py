import inspect
import os
import sys
import unittest

from threading import Event
from shutil import rmtree

 

from processflow.lib.events import EventList
from processflow.lib.jobstatus import JobStatus
from processflow.lib.util import print_message
from processflow.lib.initialize import initialize, setup_directories
from processflow.jobs.e3smdiags import E3SMDiags
from utils import mock_climos


class TestE3SM(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestE3SM, self).__init__(*args, **kwargs)
        self.event_list = EventList()
        self.config_path = 'tests/test_configs/e3sm_diags_complete.cfg'
        self.config, self.filemanager, self.runmanager = initialize(
            argv=['--test', '-c', self.config_path, '--dryrun'],
            version="2.2.0",
            branch="testing",
            event_list=self.event_list)
        
        self.config['data_types']['climo_regrid'] = {}
        self.config['data_types']['climo_regrid']['monthly'] = True

        if os.path.exists(self.config['global']['project_path']):
            rmtree(self.config['global']['project_path'])
        setup_directories(self.config)

        self.short_name = 'piControl_testing'
        self.case_name = '20180129.DECKv1b_piControl.ne30_oEC.edison'

    def test_e3sm_diags_postvalidate_fail(self):
        """
        Checks that the e3sm_diags job successfully marks a job that hasnt
        produced output as failed
        """
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')

        e3sm_diags = E3SMDiags(
            short_name=self.short_name,
            case=self.case_name,
            start=1,
            end=2,
            comparison='obs',
            config=self.config)

        self.assertFalse(
            e3sm_diags.postvalidate(
                config=self.config,
                event_list=self.event_list))

    def test_e3sm_diags_execute_dryrun(self):
        """
        test that the e3sm_diags prevalidate and prerun setup works correctly
        """
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')

        for case in self.runmanager.cases:
            for job in case['jobs']:
                if job.job_type == 'climo':
                    mock_climos(
                        job._output_path, 
                        job._regrid_path,
                        self.config,
                        self.filemanager,
                        case['case'])
                    job.status = JobStatus.COMPLETED

        self.runmanager.check_data_ready()
        self.runmanager.start_ready_jobs()

        for case in self.runmanager.cases:
            for job in case['jobs']:
                if job.job_type == 'e3sm_diags':
                    job.setup_data(
                        config=self.config,
                        filemanager=self.filemanager,
                        case=self.case_name)
                    job.execute(
                        config=self.config,
                        event_list=self.event_list,
                        dryrun=True)
                    self.assertEquals(
                        job.status,
                        JobStatus.COMPLETED)


if __name__ == '__main__':
    unittest.main()
