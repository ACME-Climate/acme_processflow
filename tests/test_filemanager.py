import os, sys
import unittest
import shutil
import inspect

from configobj import ConfigObj

if sys.path[0] != '.':
    sys.path.insert(0, os.path.abspath('.'))

from lib.filemanager import FileManager
from lib.models import DataFile
from lib.events import EventList
from lib.util import print_message
from globus_cli.services.transfer import get_client


class TestFileManager(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFileManager, self).__init__(*args, **kwargs)
        self.file_types = ['atm', 'ice', 'ocn', 'rest', 'streams.ocean', 'streams.cice', 'mpas-o_in', 'mpas-cice_in', 'meridionalHeatTransport', 'lnd']
        self.local_path = '/p/user_pub/e3sm/baldwin32/E3SM_test_data/DECKv1b_1pctCO2_complete'
        self.remote_endpoint = '9d6d994a-6d04-11e5-ba46-22000b92c6ec'
        self.remote_path = '/global/cscratch1/sd/golaz/ACME_simulations/20180215.DECKv1b_1pctCO2.ne30_oEC.edison'
        self.local_endpoint = 'a871c6de-2acd-11e7-bc7c-22000b9a448b'
        self.experiment = '20180215.DECKv1b_1pctCO2.ne30_oEC.edison'

    def test_filemanager_setup_valid_from_scratch(self):
        """
        run filemansger setup with no sta
        """

        print('\n'); print_message('---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        sta = False
        db = '{}.db'.format(inspect.stack()[0][3])
        config_path = 'tests/test_configs/valid_config_from_scratch.cfg'
        config = ConfigObj(config_path)
        experiment = '20170926.FCT2.A_WCYCL1850S.ne30_oECv3.anvil'

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
        print('\n'); print_message('---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        config_path = 'tests/test_configs/e3sm_diags_complete.cfg'
        config = ConfigObj(config_path)
        db = '{}.db'.format(inspect.stack()[0][3])

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
        run the filemanager setup with sta turned on
        """
        print('\n'); print_message('---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        config_path = 'tests/test_configs/filemanager_partial_data.cfg'
        config = ConfigObj(config_path)
        db = '{}.db'.format(inspect.stack()[0][3])

        filemanager = FileManager(
            database=db,
            event_list=EventList(),
            config=config)
        filemanager.populate_file_list()
        self.assertTrue(isinstance(filemanager, FileManager))
        self.assertTrue(os.path.exists(db))

        filemanager.update_local_status()
        filemanager.write_database()
        self.assertFalse(filemanager.all_data_local())
        
        # test that the filemanager returns correct paths
        paths = filemanager.get_file_paths_by_year(
            datatype='atm',
            case='20180129.DECKv1b_piControl.ne30_oEC.edison',
            start_year=1,
            end_year=2)
        for path in paths:
            self.assertTrue(os.path.exists(path))

        # test that the filemanager returns correct paths with no year
        paths = filemanager.get_file_paths_by_year(
            datatype='ocn_streams',
            case='20180129.DECKv1b_piControl.ne30_oEC.edison')
        for path in paths:
            self.assertTrue(os.path.exists(path))

        # test nothing is returned for incorrect yeras
        paths = filemanager.get_file_paths_by_year(
            datatype='ocn_streams',
            case='20180129.DECKv1b_piControl.ne30_oEC.edison',
            start_year=1,
            end_year=100)
        self.assertTrue(paths is None)

        # test the filemanager knows when data is ready
        ready = filemanager.check_data_ready(
            data_required=['atm'], 
            case='20180129.DECKv1b_piControl.ne30_oEC.edison',
            start_year=1,
            end_year=2)
        self.assertTrue(ready)

        # test the filemanager knows when data is NOT ready
        ready = filemanager.check_data_ready(
            data_required=['atm'], 
            case='20180129.DECKv1b_piControl.ne30_oEC.edison',
            start_year=1,
            end_year=3)
        self.assertFalse(ready)

        ready = filemanager.check_data_ready(
            data_required=['ocn_streams'], 
            case='20180129.DECKv1b_piControl.ne30_oEC.edison')
        self.assertTrue(ready)

        os.remove(db)

if __name__ == '__main__':
    unittest.main()
