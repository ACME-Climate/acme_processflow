import inspect
import os
import sys
import unittest

from threading import Event
from shutil import rmtree

from processflow.lib.jobstatus import JobStatus
from processflow.lib.initialize import initialize, setup_directories
from processflow.lib.util import print_message
from processflow.lib.events import EventList
from processflow.jobs.climo import Climo
from tests.utils import mock_climos, json_to_conf, mock_atm

PROJECT_PATH = os.path.abspath('tests/test_resources/climo_test')

class TestClimo(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestClimo, self).__init__(*args, **kwargs)

        config_json = 'tests/test_configs/valid_config_simple.json'
        self.config_path = 'tests/test_configs/valid_config_simple.cfg'
        self.case_name = '20180129.DECKv1b_piControl.ne30_oEC.edison'
        self.short_name = 'piControl_testing'
        self.event_list = EventList()

        self.project_path = PROJECT_PATH
        local_data_path = os.path.join(self.project_path, 'input')
        if os.path.exists(self.project_path):
            rmtree(self.project_path, ignore_errors=True)

        keys = {
            "global": {
                "project_path": self.project_path,
            },
            "simulations": {
                "start_year": "1",
                "end_year": "2",
                "20180129.DECKv1b_piControl.ne30_oEC.edison": {
                    "transfer_type": "local",
                    "local_path": local_data_path,
                    "short_name": "piControl",
                    "native_grid_name": "ne30",
                    "native_mpas_grid_name": "oEC60to30v3",
                    "data_types": "all",
                    "job_types": "climo"
                }
            }
        }
        json_to_conf(config_json, self.config_path, keys)
        mock_atm(1, 2, self.case_name, local_data_path)

        self.config, self.filemanager, self.runmanager = initialize(
            argv=['--test', '-c', self.config_path],
            version="2.2.0",
            branch="testing",
            event_list=self.event_list)

    def test_climo_setup(self):
        """
        Run ncclimo setup on valid config
        """
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')

        climo = Climo(
            short_name=self.short_name,
            case=self.case_name,
            start=1,
            end=2,
            config=self.config)

        self.assertEqual(
            climo.status,
            JobStatus.VALID)

    def test_climo_valid_postvalidate(self):
        """
        Test that climo.postvalidate will return true on a case thats been run
        """
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')

        climo = Climo(
            short_name=self.short_name,
            case=self.case_name,
            start=1,
            end=2,
            config=self.config)

        mock_climos(
            climo._output_path,
            climo._regrid_path,
            self.config,
            self.filemanager,
            case=self.case_name)

        self.assertTrue(
            climo.postvalidate(self.config))

    def test_climo_invalid_postvalidate(self):
        """
        Test that climo.postvalidate will return false on a case that hasnt been run
        """
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')

        climo = Climo(
            short_name=self.short_name,
            case=self.case_name,
            start=2,
            end=4,
            config=self.config)

        self.assertFalse(
            climo.postvalidate(self.config))

    def test_climo_execute_dryrun(self):
        """
        Test that ncclimo will do all proper setup in an incomplete run
        """
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')

        climo = Climo(
            short_name=self.short_name,
            case=self.case_name,
            start=1,
            end=2,
            config=self.config)

        self.assertEqual(
            climo.status,
            JobStatus.VALID)
        climo.execute(
            config=self.config,
            event_list=self.event_list,
            dryrun=True)
        self.assertEquals(
            climo.status,
            JobStatus.COMPLETED)

    def test_ncclimo_execute_completed(self):
        """
        test that if ncclimo is told to run on a project thats already completed ncclimo
        for the given yearset it will varify that the output is present and not run again
        """
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')

        climo = Climo(
            short_name=self.short_name,
            case=self.case_name,
            start=1,
            end=2,
            config=self.config)

        mock_climos(
            climo._output_path,
            climo._regrid_path,
            self.config,
            self.filemanager,
            self.case_name)

        self.assertEqual(
            climo.status,
            JobStatus.VALID)
        climo.execute(
            config=self.config,
            event_list=self.event_list,
            dryrun=True)
        self.assertTrue(
            climo.postvalidate(
                config=self.config))

def tearDownModule():
    if os.path.exists(PROJECT_PATH):
        rmtree(PROJECT_PATH, ignore_errors=True)

if __name__ == '__main__':
    unittest.main()
