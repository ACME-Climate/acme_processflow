import inspect
import os
import shutil
import sys
import threading
import unittest

from configobj import ConfigObj

 

from processflow.lib.runmanager import RunManager
from processflow.lib.filemanager import FileManager
from processflow.lib.events import EventList
from processflow.lib.util import print_message


class TestRunManager(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestRunManager, self).__init__(*args, **kwargs)

        config_path = 'tests/test_configs/runmanager_valid_many_jobs.cfg'
        self.config = ConfigObj(config_path)
        self.project_path = '/p/user_pub/e3sm/baldwin32/testing_data/'
        if not os.path.exists(self.project_path):
            os.makedirs(self.project_path)
        self.output_path = os.path.join(
            self.project_path,
            'output')
        self.input_path = os.path.join(
            self.project_path,
            'input')
        self.run_scripts_path = os.path.join(
            self.project_path,
            'output',
            'run_scripts')
        self.mutex = threading.Lock()
        self.remote_endpoint = '9d6d994a-6d04-11e5-ba46-22000b92c6ec'
        self.remote_path = '/global/cscratch1/sd/sbaldwin/1pct'
        self.experiment = '20180129.DECKv1b_piControl.ne30_oEC.edison'
        self.local_endpoint = 'a871c6de-2acd-11e7-bc7c-22000b9a448b'
        self.config['global']['output_path'] = self.output_path
        self.config['global']['input_path'] = self.input_path
        self.config['global']['run_scripts_path'] = self.run_scripts_path
        self.config['global']['resource_dir'] = os.path.abspath('./resources')
        self.config['simulations']['start_year'] = int(self.config['simulations']['start_year'])
        self.config['simulations']['end_year'] = int(self.config['simulations']['end_year'])
        self.config['global']['host'] = False

    def test_runmanager_setup(self):
        """
        Run the runmanager setup
        """
        print '\n'; print_message('---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')

        db_path = os.path.join(
            self.project_path,
            '{}.db'.format(inspect.stack()[0][3]))
        if os.path.exists(self.project_path):
            shutil.rmtree(self.project_path)
        os.makedirs(self.project_path)
        filemanager = FileManager(
            event_list=EventList(),
            database=db_path,
            config=self.config)
        
        runmanager = RunManager(
            event_list=EventList(),
            config=self.config,
            filemanager=filemanager)
        runmanager.setup_cases()

        self.assertEqual(len(runmanager.cases), 1)
        for case in runmanager.cases:
            self.assertEqual(len(case['jobs']), 10)

            num_climo = 0
            num_ts = 0
            num_regrid = 0
            num_e3sm = 0
            num_amwg = 0
            num_cmor = 0
            for job in case['jobs']:
                if job.job_type == 'climo':
                    num_climo += 1
                elif job.job_type == 'timeseries':
                    num_ts += 1
                elif job.job_type == 'regrid':
                    num_regrid += 1
                elif job.job_type == 'e3sm_diags':
                    num_e3sm += 1
                elif job.job_type == 'amwg':
                    num_amwg += 1
                elif job.job_type == 'cmor':
                    num_cmor += 1

            self.assertEqual(num_climo, 1)
            self.assertEqual(num_ts, 3)
            self.assertEqual(num_regrid, 3)
            self.assertEqual(num_cmor, 1)
            self.assertEqual(num_e3sm, 1)
            self.assertEqual(num_amwg, 1)


    def test_runmanager_write_job_state(self):
        print '\n'; print_message('---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        db_path = os.path.join(
            self.project_path,
            '{}.db'.format(inspect.stack()[0][3]))
        if os.path.exists(self.project_path):
            shutil.rmtree(self.project_path)
        os.makedirs(self.project_path)
        filemanager = FileManager(
            event_list=EventList(),
            database=db_path,
            config=self.config)
        
        runmanager = RunManager(
            event_list=EventList(),
            config=self.config,
            filemanager=filemanager)
        runmanager.setup_cases()

        path = os.path.join(self.project_path, 'output', 'job_state.txt')
        runmanager.write_job_sets(path)
        self.assertTrue(os.path.exists(path))
        os.remove(db_path)


if __name__ == '__main__':
    unittest.main()
