import inspect
import os
import sys
import unittest

from configobj import ConfigObj

 

from processflow.lib.verify_config import verify_config
from processflow.lib.util import print_message


class TestVerifyConfig(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestVerifyConfig, self).__init__(*args, **kwargs)

    def test_valid(self):
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        config_path = 'tests/test_configs/amwg_complete.cfg'
        config = ConfigObj(config_path)
        messages = verify_config(config)
        self.assertEquals(len(messages), 0)

    def test_invalid_missing_lnd_data(self):
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        config_path = 'tests/test_configs/invalid_config_missing_lnd.cfg'
        config = ConfigObj(config_path)
        messages = verify_config(config)
        self.assertTrue(
            '20180129.DECKv1b_piControl.ne30_oEC.edison is set to use data_type lnd, but this data type is not in the data_types config option' in messages)

    def test_invalid_missing_climo(self):
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        config_path = 'tests/test_configs/invalid_config_missing_climo.cfg'
        config = ConfigObj(config_path)
        messages = verify_config(config)
        self.assertTrue(
            'amwg is set to run at frequency 2 but no climo job for this frequency is set' in messages)

    def test_invalid_missing_global(self):
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        config_path = 'tests/test_configs/invalid_config_no_global.cfg'
        config = ConfigObj(config_path)
        messages = verify_config(config)
        self.assertTrue('No global section found in config' in messages)
        self.assertTrue('No simulations section found in config' in messages)

    def test_invalid_missing_project(self):
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        config_path = 'tests/test_configs/invalid_config_no_project_path.cfg'
        config = ConfigObj(config_path)
        messages = verify_config(config)
        self.assertTrue('no project_path in global options' in messages)
        self.assertTrue('No data_types section found in config' in messages)

    def test_invalid_bad_transfer(self):
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        config_path = 'tests/test_configs/invalid_config_bad_transfer.cfg'
        config = ConfigObj(config_path)
        messages = verify_config(config)

        self.assertTrue(
            '20180129.DECKv1b_piControl.ne30_oEC.edison is missing trasfer_type, if the data is local, set transfer_type to \'local\'' in messages)
        self.assertTrue(
            'case test.case.2 is set for local data, but no local_path is set' in messages)
        self.assertTrue(
            'no data_types found for test.case.2, set to \'all\' to select all types, or list only data_types desired' in messages)
        self.assertTrue(
            'case test.case.3 has transfer_type of sftp, but is missing remote_hostname' in messages)
        self.assertTrue(
            'case test.case.3 has non-local data, but no remote_path given' in messages)
        self.assertTrue(
            'case test.case.4 has transfer_type of globus, but is missing remote_uuid' in messages)
        self.assertTrue(
            'case test.case.4 is set to use globus, but no local_globus_uuid was set in the global options' in messages)

    def test_invalid_bad_job_type(self):
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        config_path = 'tests/test_configs/invalid_config_bad_job_type.cfg'
        config = ConfigObj(config_path)
        messages = verify_config(config)
        self.assertTrue(
            '20180129.DECKv1b_piControl.ne30_oEC.edison is set to run job beepboop, but this run type is not in either the post-processing or diags config sections' in messages)

    def test_invalid_bad_data_type(self):
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        config_path = 'tests/test_configs/invalid_config_bad_data_type.cfg'
        config = ConfigObj(config_path)
        messages = verify_config(config)
        self.assertTrue('atm has no file_format' in messages)
        self.assertFalse('atm has no remote_path' in messages)
        self.assertTrue('atm has no local_path' in messages)

    def test_invalid_bad_regrid(self):
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        config_path = 'tests/test_configs/invalid_config_bad_regrid.cfg'
        config = ConfigObj(config_path)
        messages = verify_config(config)
        self.assertTrue('no source_grid_path given for lnd regrid' in messages)
        self.assertTrue(
            'no destination_grid_path given for lnd regrid' in messages)
        self.assertTrue(
            'no destination_grid_name given for lnd regrid' in messages)
        self.assertTrue(
            'regrid is set to run on data_type ocn, but this type is not set in simulation 20180129.DECKv1b_piControl.ne30_oEC.edison' in messages)


if __name__ == '__main__':
    unittest.main()
