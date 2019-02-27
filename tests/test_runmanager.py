import os
import sys
import threading
import unittest
import shutil
import inspect

from configobj import ConfigObj

if sys.path[0] != '.':
    sys.path.insert(0, os.path.abspath('.'))

from lib.runmanager import RunManager
from lib.filemanager import FileManager
from lib.models import DataFile
from lib.events import EventList
from lib.util import print_message

class TestRunManager(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestRunManager, self).__init__(*args, **kwargs)
        config_path = os.path.join(
            os.getcwd(),
            'tests',
            'test_configs',
            'test_run_no_sta.cfg')
        self.config = ConfigObj(config_path)
        self.project_path = '/p/user_pub/e3sm/baldwin32/E3SM_test_data/DECKv1b_1pctCO2_not_complete'
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
        self.remote_path = '/global/cscratch1/sd/golaz/ACME_simulations/20180215.DECKv1b_1pctCO2.ne30_oEC.edison'
        self.experiment = '20180215.DECKv1b_1pctCO2.ne30_oEC.edison'
        self.local_endpoint = 'a871c6de-2acd-11e7-bc7c-22000b9a448b'
        self.config['global']['output_path'] = self.output_path
        self.config['global']['input_path'] = self.input_path
        self.config['global']['run_scripts_path'] = self.run_scripts_path
        self.config['global']['resource_dir'] = os.path.abspath('./resources')

    def test_runmanager_setup(self):
        """
        Run the runmanager setup
        """
        print('\n'); print_message('---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')

        db_path = os.path.join(
            self.project_path,
            '{}.db'.format(inspect.stack()[0][3]))
        if os.path.exists(self.project_path):
            shutil.rmtree(self.project_path)
        os.makedirs(self.project_path)
        filemanager = FileManager(
            ui=False,
            event_list=EventList(),
            database=db_path,
            types=['atm'],
            sta=False,
            mutex=self.mutex,
            remote_endpoint=self.remote_endpoint,
            remote_path=self.remote_path,
            local_endpoint=self.local_endpoint,
            local_path=self.project_path,
            experiment=self.experiment)
        runmanager = RunManager(
            short_name='testname',
            account='',
            resource_path='./resources',
            ui=False,
            event_list=EventList(),
            output_path=self.output_path,
            caseID=self.experiment,
            scripts_path=self.run_scripts_path,
            thread_list=[],
            event=threading.Event(),
            no_host=True,
            url_prefix='',
            always_copy=False)
        runmanager.setup_job_sets(
            set_frequency=[5, 10],
            sim_start_year=int(self.config['global']['simulation_start_year']),
            sim_end_year=int(self.config['global']['simulation_end_year']),
            config=self.config,
            filemanager=filemanager)

        self.assertEqual(len(runmanager.job_sets), 1)
        for job_set in runmanager.job_sets:
            if job_set.set_number == 1:
                self.assertEqual(job_set.length, 5)
                self.assertEqual(job_set.set_start_year, 1)
                self.assertEqual(job_set.set_end_year, 5)
                job_names = job_set.get_job_names()
                self.assertTrue('ncclimo' in job_names)
                self.assertTrue('timeseries' in job_names)
                self.assertTrue('aprime_diags' in job_names)
                self.assertTrue('e3sm_diags' in job_names)


    def test_runmanager_write(self):
        print('\n'); print_message('---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        db_path = os.path.join(
            self.project_path,
            '{}.db'.format(inspect.stack()[0][3]))
        if os.path.exists(db_path):
            os.remove(db_path)

        local_path = '/p/user_pub/e3sm/baldwin32/E3SM_test_data/DECKv1b_1pctCO2_complete'
        database = '{}.db'.format(inspect.stack()[0][3])
        local_path = os.path.join(
            self.project_path,
            'input')
        types = ['atm']
        mutex = threading.Lock()
        filemanager = FileManager(
            mutex=mutex,
            event_list=EventList(),
            sta=False,
            types=types,
            database=database,
            remote_endpoint=self.remote_endpoint,
            remote_path=self.remote_path,
            local_endpoint=self.local_endpoint,
            local_path=local_path,
            experiment=self.experiment)

        self.assertTrue(isinstance(filemanager, FileManager))
        runmanager = RunManager(
            short_name='testname',
            account='',
            resource_path='./resources',
            ui=False,
            event_list=EventList(),
            output_path=self.output_path,
            caseID=self.experiment,
            scripts_path=self.run_scripts_path,
            thread_list=[],
            event=threading.Event(),
            no_host=True,
            url_prefix='',
            always_copy=False)
        runmanager.setup_job_sets(
            set_frequency=[5, 10],
            sim_start_year=int(self.config['global']['simulation_start_year']),
            sim_end_year=int(self.config['global']['simulation_end_year']),
            config=self.config,
            filemanager=filemanager)
        path = os.path.join(self.project_path, 'output', 'job_state.txt')
        runmanager.write_job_sets(path)
        self.assertTrue(os.path.exists(path))
        os.remove(database)


if __name__ == '__main__':
    unittest.main()
