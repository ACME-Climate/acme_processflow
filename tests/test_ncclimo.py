import os
import sys
import unittest
import inspect
from configobj import ConfigObj

if sys.path[0] != '.':
    sys.path.insert(0, os.path.abspath('.'))

from jobs.Ncclimo import Climo as Ncclimo
from jobs.JobStatus import JobStatus
from lib.events import EventList
from lib.util import print_message

class TestNcclimo(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestNcclimo, self).__init__(*args, **kwargs)
        config_path = os.path.join(
            os.getcwd(), 'tests', 'test_configs', 'test_run_no_sta.cfg')
        self.config = ConfigObj(config_path)
        self.project_path = os.path.join(os.getcwd(), '..', 'testproject')

    def test_ncclimo_setup(self):
        """
        Run ncclimo setup on valid config
        """
        print('\n'); print_message('---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        config = {
            'account': '',
            'year_set': 1,
            'start_year': 50,
            'end_year': 55,
            'caseId': self.config['global']['experiment'],
            'annual_mode': 'sdd',
            'input_directory': os.path.join(self.project_path, 'input'),
            'climo_output_directory': os.path.join(self.config['global']['project_path'], 'output', 'pp', 'ne30', 'climo', '5yr'),
            'regrid_output_directory': os.path.join(self.config['global']['project_path'], 'output', 'pp', 'fv129x256', 'climo', '5yr'),
            'regrid_map_path': self.config['ncclimo']['regrid_map_path'],
            'year_set': 1,
            'run_scripts_path': os.path.join(self.project_path, 'output', 'run_scripts')
        }
        ncclimo = Ncclimo(
            config=config,
            event_list=EventList())
        self.assertEqual(ncclimo.status.name, 'VALID')

    def test_ncclimo_valid_prevalidate(self):
        """
        Test that valid input config will be marked as valid by the job
        """
        print('\n'); print_message('---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        config = {
            'account': '',
            'year_set': 1,
            'start_year': 50,
            'end_year': 55,
            'caseId': self.config['global']['experiment'],
            'annual_mode': 'sdd',
            'input_directory': os.path.join(self.project_path, 'input'),
            'climo_output_directory': os.path.join(self.config['global']['project_path'], 'output', 'pp', 'ne30', 'climo', '5yr'),
            'regrid_output_directory': os.path.join(self.config['global']['project_path'], 'output', 'pp', 'fv129x256', 'climo', '5yr'),
            'regrid_map_path': self.config['ncclimo']['regrid_map_path'],
            'year_set': 1,
            'run_scripts_path': os.path.join(self.project_path, 'output', 'run_scripts')
        }
        ncclimo = Ncclimo(
            config=config,
            event_list=EventList())
        ncclimo.status = JobStatus.VALID
        self.assertFalse(ncclimo.prevalidate(config))

    def test_ncclimo_missing_input(self):
        """
        Test that a missing input item will invalidate the job
        """
        print('\n'); print_message('---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        config = {
            'account': '',
            'year_set': 1,
            'start_year': 50,
            'end_year': 55,
            'caseId': self.config['global']['experiment'],
            'annual_mode': 'sdd',
            #'input_directory': os.path.join(self.project_path, 'input'),
            'climo_output_directory': os.path.join(self.config['global']['project_path'], 'output', 'pp', 'ne30', 'climo', '5yr'),
            'regrid_output_directory': os.path.join(self.config['global']['project_path'], 'output', 'pp', 'fv129x256', 'climo', '5yr'),
            'regrid_map_path': self.config['ncclimo']['regrid_map_path'],
            'year_set': 1,
            'run_scripts_path': os.path.join(self.project_path, 'output', 'run_scripts')
        }
        ncclimo = Ncclimo(
            config=config,
            event_list=EventList())
        self.assertEqual(ncclimo.status.name, 'INVALID')

    def test_ncclimo_execute_not_completed(self):
        """
        Test that ncclimo will do all proper setup in an incomplete run
        """
        print('\n'); print_message('---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        start_year = 51
        end_year = 55
        self.config['global']['project_path'] = '/p/user_pub/e3sm/baldwin32/E3SM_test_data/DECKv1b_1pctCO2_not_complete'
        self.config['global']['exeriment'] = '20171011.beta2_FCT2-icedeep_branch.A_WCYCL1850S.ne30_oECv3_ICG.edison'
        year_set_string = '{start:04d}-{end:04d}'.format(
            start=start_year,
            end=end_year)
        config = {
            'account': '',
            'year_set': 1,
            'start_year': start_year,
            'end_year': end_year,
            'caseId': self.config['global']['experiment'],
            'annual_mode': 'sdd',
            'input_directory': os.path.join(self.config['global']['project_path'], 'input', 'atm'),
            'climo_output_directory': os.path.join(self.config['global']['project_path'], 'output', 'pp', 'ne30', 'climo', '5yr'),
            'regrid_output_directory': os.path.join(self.config['global']['project_path'], 'output', 'pp', 'fv129x256', 'climo', '5yr'),
            'regrid_map_path': self.config['ncclimo']['regrid_map_path'],
            'year_set': 1,
            'run_scripts_path': os.path.join(self.config['global']['project_path'], 'output', 'run_scripts')
        }
        ncclimo = Ncclimo(
            config=config,
            event_list=EventList())
        self.assertEqual(ncclimo.status, JobStatus.VALID)
        self.assertFalse(ncclimo.execute(dryrun=True))
        self.assertEqual(ncclimo.status.name, 'COMPLETED')

    def test_ncclimo_execute_completed(self):
        """
        test that if ncclimo is told to run on a project thats already completed ncclimo
        for the given yearset it will varify that the output is present and not run again
        """
        print('\n'); print_message('---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        start_year = 1
        end_year = 10
        # REAL DATA
        project_path = '/p/user_pub/e3sm/baldwin32/E3SM_test_data/DECKv1b_1pctCO2_complete'
        year_set_string = '{start:04d}-{end:04d}'.format(
            start=start_year,
            end=end_year)
        config = {
            'account': '',
            'year_set': 1,
            'start_year': start_year,
            'end_year': end_year,
            'caseId': '20180129.DECKv1b_piControl.ne30_oEC.edison',
            'annual_mode': 'sdd',
            'input_directory': os.path.join(project_path, 'input', 'atm'),
            'climo_output_directory': os.path.join(project_path, 'output', 'pp', 'ne30', 'climo', '10yr'),
            'regrid_output_directory': os.path.join(project_path, 'output', 'pp', 'fv129x256', 'climo', '10yr'),
            'regrid_map_path': self.config['ncclimo']['regrid_map_path'],
            'year_set': 1,
            'run_scripts_path': os.path.join(project_path, 'output', 'run_scripts')
        }
        ncclimo = Ncclimo(
            config=config,
            event_list=EventList())
        self.assertEqual(ncclimo.status, JobStatus.VALID)
        ncclimo.execute(dryrun=True)
        self.assertTrue(ncclimo.postvalidate())

    def test_ncclimo_execute_bad_year(self):
        """
        test that if given the wrong input year ncclimo will exit correctly
        """
        print('\n'); print_message('---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        start_year = 55
        end_year = 60
        self.config['global']['project_path'] = '/p/user_pub/e3sm/baldwin32/E3SM_test_data/DECKv1b_1pctCO2_complete'
        self.config['global']['exeriment'] = '20180215.DECKv1b_1pctCO2.ne30_oEC.edison'
        year_set_string = '{start:04d}-{end:04d}'.format(
            start=start_year,
            end=end_year)
        config = {
            'account': '',
            'year_set': 1,
            'start_year': start_year,
            'end_year': end_year,
            'caseId': self.config['global']['experiment'],
            'annual_mode': 'sdd',
            'input_directory': os.path.join(self.config['global']['project_path'], 'input', 'atm'),
            'climo_output_directory': os.path.join(self.config['global']['project_path'], 'output', 'climo', '5yr'),
            'regrid_output_directory': os.path.join(self.config['global']['project_path'], 'output', 'climo_regrid'),
            'regrid_map_path': self.config['ncclimo']['regrid_map_path'],
            'year_set': 1,
            'run_scripts_path': os.path.join(self.config['global']['project_path'], 'output', 'run_scripts')
        }
        ncclimo = Ncclimo(
            config=config,
            event_list=EventList())
        self.assertEqual(ncclimo.status, JobStatus.VALID)
        self.assertFalse(ncclimo.postvalidate())

    def test_ncclimo_execute_bad_regrid_dir(self):
        print('\n'); print_message('---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        start_year = 56
        end_year = 60
        self.config['global']['project_path'] = '/p/cscratch/acme/baldwin32/20171016/'
        self.config['global']['exeriment'] = '20171011.beta2_FCT2-icedeep_branch.A_WCYCL1850S.ne30_oECv3_ICG.edison'
        year_set_string = '{start:04d}-{end:04d}'.format(
            start=start_year,
            end=end_year)
        config = {
            'account': '',
            'year_set': 1,
            'start_year': start_year,
            'end_year': end_year,
            'caseId': self.config['global']['experiment'],
            'annual_mode': 'sdd',
            'input_directory': os.path.join(self.config['global']['project_path'], 'input', 'atm'),
            'climo_output_directory': os.path.join(self.config['global']['project_path'], 'output', 'climo', '5yr'),
            'regrid_output_directory': os.path.join(self.config['global']['project_path'], 'output', 'XXYYZZ'),
            'regrid_map_path': self.config['ncclimo']['regrid_map_path'],
            'year_set': 1,
            'run_scripts_path': os.path.join(self.config['global']['project_path'], 'output', 'run_scripts')
        }
        ncclimo = Ncclimo(
            config=config,
            event_list=EventList())
        self.assertEqual(ncclimo.status, JobStatus.VALID)
        self.assertFalse(ncclimo.postvalidate())

    def test_ncclimo_execute_bad_climo_dir(self):
        """
        test that ncclimo will correctly exit if given a non-existant climo dir
        """
        print('\n'); print_message('---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        start_year = 56
        end_year = 60
        self.config['global']['project_path'] = '/p/cscratch/acme/baldwin32/20171016/'
        self.config['global']['exeriment'] = '20171011.beta2_FCT2-icedeep_branch.A_WCYCL1850S.ne30_oECv3_ICG.edison'
        year_set_string = '{start:04d}-{end:04d}'.format(
            start=start_year,
            end=end_year)
        config = {
            'account': '',
            'year_set': 1,
            'start_year': start_year,
            'end_year': end_year,
            'caseId': self.config['global']['experiment'],
            'annual_mode': 'sdd',
            'input_directory': os.path.join(self.config['global']['project_path'], 'input', 'atm'),
            'climo_output_directory': os.path.join(self.config['global']['project_path'], 'output', 'climo', 'XXYYZZ'),
            'regrid_output_directory': os.path.join(self.config['global']['project_path'], 'output', 'climo_regrid'),
            'regrid_map_path': self.config['ncclimo']['regrid_map_path'],
            'year_set': 1,
            'run_scripts_path': os.path.join(self.config['global']['project_path'], 'output', 'run_scripts')
        }
        ncclimo = Ncclimo(
            config=config,
            event_list=EventList())
        self.assertEqual(ncclimo.status, JobStatus.VALID)
        self.assertFalse(ncclimo.postvalidate())


if __name__ == '__main__':
    unittest.main()
