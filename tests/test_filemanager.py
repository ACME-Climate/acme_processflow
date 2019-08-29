import inspect
import os
import sys
import threading
import unittest

from configobj import ConfigObj
from shutil import rmtree

from processflow.lib.filemanager import FileManager
from processflow.lib.events import EventList
from processflow.lib.util import print_message
from processflow.lib.initialize import initialize
from tests.utils import json_to_conf, mock_atm

PROJECT_PATH = os.path.abspath('tests/test_resources/filemanager_test')

class TestFileManager(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFileManager, self).__init__(*args, **kwargs)
        self.file_types = ['atm', 'ice', 'ocn', 'ocn_restart', 'cice_restart', 'streams.ocean',
                           'streams.cice', 'mpas-o_in', 'mpas-cice_in', 'meridionalHeatTransport', 'lnd']

        config_json = 'tests/test_configs/valid_config_all_data.json'
        self.config_path = 'tests/test_configs/valid_config_all_data.cfg'
        self.case_name = '20180129.DECKv1b_piControl.ne30_oEC.edison'
        self.short_name = 'piControl_testing'
        self.event_list = EventList()

        self.project_path = PROJECT_PATH
        local_data_path = os.path.join('tests/test_resources/mock_data')
        if os.path.exists(self.project_path):
            rmtree(self.project_path, ignore_errors=True)
        keys = {
            "global": {
                "project_path": self.project_path,
            },
            "simulations": {
                "start_year": "1",
                "end_year": "1",
                self.case_name: {
                    "transfer_type": "local",
                    "local_path": local_data_path,
                    "short_name": self.short_name,
                    "native_grid_name": "ne30",
                    "native_mpas_grid_name": "oEC60to30v3",
                    "data_types": self.file_types,
                    "job_types": "all"
                }
            }
        }
        json_to_conf(config_json, self.config_path, keys)
    
    def tearDownModule(self):
        if os.path.exists(self.project_path):
            rmtree(self.project_path, ignore_errors=True)

    def test_filemanager_setup_valid_from_scratch(self):
        """
        run filemansger setup from scratch
        """

        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        db = 'tests/test_resources/{}.db'.format(inspect.stack()[0][3])
        config = ConfigObj(self.config_path)

        filemanager = FileManager(
            database=db,
            event_list=EventList(),
            config=config)

        self.assertTrue(isinstance(filemanager, FileManager))
        self.assertTrue(os.path.exists(db))
        os.remove(db)

    def test_filemanager_setup_valid_with_inplace_data(self):
        """
        run the filemanager setup with sta turned on
        """
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        config = ConfigObj(self.config_path)
        db = 'tests/test_resources/{}.db'.format(inspect.stack()[0][3])

        filemanager = FileManager(
            database=db,
            event_list=EventList(),
            config=config)
        filemanager.populate_file_list()
        filemanager.update_local_status()

        self.assertTrue(isinstance(filemanager, FileManager))
        self.assertTrue(os.path.exists(db))
        self.assertTrue(filemanager.all_data_local())
        os.remove(db)

    def test_filemanager_get_file_paths(self):
        """
        run the filemanager setup with short term archive turned on
        """
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        db = 'tests/test_resources/{}.db'.format(inspect.stack()[0][3])

        pargv = ['--test', '-c', self.config_path]
        config, _, _ = initialize(
            argv=pargv,
            version='2.2.0',
            branch='__testing__',
            event_list=EventList())

        filemanager = FileManager(
            database=db,
            event_list=EventList(),
            config=config)
        filemanager.populate_file_list()
        self.assertTrue(isinstance(filemanager, FileManager))
        self.assertTrue(os.path.exists(db))

        filemanager.update_local_status()
        filemanager.write_database()

        self.assertTrue(filemanager.all_data_local())

        # test that the filemanager returns correct paths
        paths = filemanager.get_file_paths_by_year(
            datatype='atm',
            case='20180129.DECKv1b_piControl.ne30_oEC.edison',
            start_year=1,
            end_year=1)
        for path in paths:
            self.assertTrue(os.path.exists(path))

        # test that the filemanager returns correct paths with no year
        paths = filemanager.get_file_paths_by_year(
            datatype='ocn',
            case='20180129.DECKv1b_piControl.ne30_oEC.edison')
        for path in paths:
            self.assertTrue(os.path.exists(path))

        # test that the filemanager returns as much data as possible
        paths = filemanager.get_file_paths_by_year(
            datatype='ocn',
            case='20180129.DECKv1b_piControl.ne30_oEC.edison',
            start_year=1,
            end_year=3)
        self.assertTrue(len(paths) == 12)

        # test the filemanager knows when data is ready
        ready = filemanager.check_data_ready(
            data_required=['atm'],
            case='20180129.DECKv1b_piControl.ne30_oEC.edison',
            start_year=1,
            end_year=1)
        self.assertTrue(ready)

        # test the filemanager knows when data is NOT ready
        ready = filemanager.check_data_ready(
            data_required=['dummy'],
            case='20180129.DECKv1b_piControl.ne30_oEC.edison',
            start_year=1,
            end_year=1)
        self.assertFalse(ready)

        ready = filemanager.check_data_ready(
            data_required=['ocn'],
            case='20180129.DECKv1b_piControl.ne30_oEC.edison')
        self.assertTrue(ready)

        os.remove(db)

def tearDownModule():
    if os.path.exists(PROJECT_PATH):
        rmtree(PROJECT_PATH, ignore_errors=True)

if __name__ == '__main__':
    unittest.main()
