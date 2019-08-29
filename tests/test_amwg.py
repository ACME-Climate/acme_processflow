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
from processflow.jobs.amwg import AMWG
from utils import mock_climos, json_to_conf, mock_atm

PROJECT_PATH = os.path.abspath('tests/test_resources/amwg_test')

class TestAMWG(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestAMWG, self).__init__(*args, **kwargs)

        self.event_list = EventList()
        
        self.project_path = PROJECT_PATH
        if os.path.exists(self.project_path):
            rmtree(self.project_path, ignore_errors=True)

        config_json = 'tests/test_configs/amwg_complete.json'
        self.config_path = 'tests/test_configs/amwg_complete.cfg'

        local_data_path = os.path.join(self.project_path, 'input')
        keys = {
            "global": {
                "project_path": self.project_path,
                "email": "",
            },
            "simulations": {
                "start_year": "1",
                "end_year": "2",
                "20180129.DECKv1b_piControl.ne30_oEC.edison": {
                    "transfer_type": "local",
                    "local_path": local_data_path,
                    "short_name": "testing_piControl",
                    "native_grid_name": "ne30",
                    "native_mpas_grid_name": "oEC60to30v3",
                    "data_types": "all",
                    "job_types": "all",
                    "comparisons": "obs"
                },
                "20180215.DECKv1b_1pctCO2.ne30_oEC.edison": {
                    "transfer_type": "local",
                    "local_path": local_data_path,
                    "short_name": "testing_1pctCO2",
                    "native_grid_name": "ne30",
                    "native_mpas_grid_name": "oEC60to30v3",
                    "data_types": "all",
                    "job_types": "all",
                    "comparisons": "20180129.DECKv1b_piControl.ne30_oEC.edison"
                }
            }
        }
        json_to_conf(config_json, self.config_path, keys)
        mock_atm(1, 2, "20180215.DECKv1b_1pctCO2.ne30_oEC.edison", local_data_path)
        mock_atm(1, 2, "20180129.DECKv1b_piControl.ne30_oEC.edison", local_data_path)

        self.config, self.filemanager, self.runmanager = initialize(
            argv=['--test', '-c', self.config_path, '--dryrun'],
            version="2.2.0",
            branch="testing",
            event_list=self.event_list)

        setup_directories(self.config)

        self.case_name = '20180129.DECKv1b_piControl.ne30_oEC.edison'
        self.short_name = 'piControl_testing'
    
    def tearDownModule(self):
        if os.path.exists(self.project_path):
            rmtree(self.project_path, ignore_errors=True)

    def test_amwg_setup(self):
        """
        Test the amwg initialization and data setup works correctly
        """

        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')

        amwg = AMWG(
            short_name=self.short_name,
            case=self.case_name,
            start=1,
            end=2,
            comparison='obs',
            config=self.config)

        self.assertEqual(
            amwg.short_name, self.short_name)
        self.assertEqual(
            amwg.start_year, 1)
        self.assertEqual(
            amwg.end_year, 2)
        self.assertIsNotNone(amwg.id)
        self.assertEqual(
            amwg.status, JobStatus.VALID)

    def test_amwg_prevalidate_valid(self):
        """
        test that amwg prevalidate returns true when all its input data is ready
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
                        job.case)
                    job.status = JobStatus.COMPLETED

        amwg = AMWG(
            short_name=self.short_name,
            case=self.case_name,
            start=1,
            end=2,
            comparison='obs',
            config=self.config)
        amwg.check_data_ready(
            self.filemanager)
        self.assertTrue(amwg.data_ready)

        amwg.setup_data(
            config=self.config,
            filemanager=self.filemanager,
            case=self.case_name)

        self.assertTrue(amwg.prevalidate())
    
    def test_amwg_prevalidate_invalid(self):
        """
        test that amwg prevalidate returns false when its input isnt ready
        """
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')

        amwg = AMWG(
            short_name=self.short_name,
            case=self.case_name,
            start=1,
            end=2,
            comparison='obs',
            config=self.config)

        self.assertFalse(amwg.data_ready)
        self.assertFalse(amwg.prevalidate())

    def test_amwg_execution_completed_job(self):
        """
        test that when run on a completed set of jobs, amwg recognizes that the run has already
        taken place and doesnt start again
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
                        job.case)
                    job.status = JobStatus.COMPLETED

        self.runmanager.check_data_ready()
        self.runmanager.start_ready_jobs()

        for case in self.runmanager.cases:
            for job in case['jobs']:
                if job.job_type == 'amwg':
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

def tearDownModule():
    if os.path.exists(PROJECT_PATH):
        rmtree(PROJECT_PATH, ignore_errors=True)

if __name__ == '__main__':
    unittest.main()
