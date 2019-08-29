import inspect
import os
import shutil
import sys
import threading
import unittest

 

from processflow.lib.util import print_message
from processflow.lib.events import EventList
from processflow.lib.initialize import initialize, parse_args

__version__ = '2.0.0'
__branch__ = 'master'


class TestInitialize(unittest.TestCase):
    """
    A test class for validating the project setup

    These tests should be run from the main project directory
    """

    def __init__(self, *args, **kwargs):
        super(TestInitialize, self).__init__(*args, **kwargs)

    def test_parse_args_valid(self):
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        argv = ['-c', 'tests/test_configs/valid_config_simple.cfg',
                '-l', 'pflow.log',
                '-r', 'resources/',
                '-m', '999',
                '--debug',
                '--dryrun']
        pargs = parse_args(argv)
        self.assertEqual(
            pargs.config, 'tests/test_configs/valid_config_simple.cfg')
        self.assertEqual(pargs.resource_path, 'resources/')
        self.assertEqual(pargs.log, 'pflow.log')
        self.assertEqual(pargs.max_jobs, 999)
        self.assertTrue(pargs.debug)
        self.assertTrue(pargs.dryrun)
        self.assertFalse(pargs.always_copy)

    def test_parse_args_print_help(self):
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        argv = ['-h']
        with self.assertRaises(SystemExit) as exitexception:
            pargs = parse_args(argv)
        self.assertEqual(exitexception.exception.code, 0)

        argv = []
        pargs = parse_args(argv, print_help=True)
        self.assertEqual(pargs, None)

    def test_init_print_version(self):
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        argv = ['-v']
        with self.assertRaises(SystemExit) as exitexception:
            a, b, c = initialize(argv=argv, version=__version__)
        self.assertEqual(exitexception.exception.code, 0)

    def test_init_no_config(self):
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        argv = []
        a, b, c = initialize(argv=argv)
        self.assertEqual(a, False)
        self.assertEqual(b, False)
        self.assertEqual(c, False)

    def test_init_valid_config_simple(self):
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        pargv = ['--test', '-c',
                 'tests/test_configs/valid_config_simple.cfg']
        _, _, _ = initialize(
            argv=pargv,
            version=__version__,
            branch=__branch__,
            event_list=EventList())

    def test_init_config_doesnt_exist_simple(self):
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        pargv = ['--test', '-c',
                 'tests/test_configs/this_file_doesnt_exist.cfg']
        config, filemanager, runmanager = initialize(
            argv=pargv,
            version=__version__,
            branch=__branch__,
            event_list=EventList())

        self.assertEqual(config, False)
        self.assertEqual(filemanager, False)
        self.assertEqual(runmanager, False)

    def test_init_config_no_white_space_simple(self):
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        pargv = ['--test', '-c',
                 'tests/test_configs/invalid_config_no_white_space.cfg']
        config, filemanager, runmanager = initialize(
            argv=pargv,
            version=__version__,
            branch=__branch__,
            event_list=EventList())

        self.assertEqual(config, False)
        self.assertEqual(filemanager, False)
        self.assertEqual(runmanager, False)

    def test_init_cant_parse_config(self):
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        pargv = ['--test', '-c',
                 'tests/test_configs/invalid_config_cant_parse.cfg']
        config, filemanager, runmanager = initialize(
            argv=pargv,
            version=__version__,
            branch=__branch__,
            event_list=EventList())

        self.assertEqual(config, False)
        self.assertEqual(filemanager, False)
        self.assertEqual(runmanager, False)

    def test_init_missing_lnd(self):
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        pargv = ['--test', '-c',
                 'tests/test_configs/invalid_config_missing_lnd.cfg']
        config, filemanager, runmanager = initialize(
            argv=pargv,
            version=__version__,
            branch=__branch__,
            event_list=EventList())

        self.assertEqual(config, False)
        self.assertEqual(filemanager, False)
        self.assertEqual(runmanager, False)

    def test_init_from_scratch_config(self):
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        pargv = ['--test', '-c', 'tests/test_configs/valid_config_from_scratch.cfg',
                 '-m', '1']
        project_path = '/p/user_pub/e3sm/baldwin32/testing/empty/'
        if os.path.exists(project_path):
            shutil.rmtree(project_path)

        config, filemanager, runmanager = initialize(
            argv=pargv,
            version=__version__,
            branch=__branch__,
            event_list=EventList())

        self.assertNotEqual(config, False)
        self.assertNotEqual(filemanager, False)
        self.assertNotEqual(runmanager, False)

        self.assertEqual(os.path.exists(project_path), True)
        if os.path.exists(project_path):
            shutil.rmtree(project_path)

    def test_init_from_scratch_config_bad_project_dir(self):
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        pargv = ['--test', '-c',
                 'tests/test_configs/valid_config_from_scratch_bad_project_path.cfg']
        project_path = '/usr/testing/'
        with self.assertRaises(SystemExit) as exitexception:
            config, filemanager, runmanager = initialize(
                argv=pargv,
                version=__version__,
                branch=__branch__,
                event_list=EventList())

            self.assertEqual(config, False)
            self.assertEqual(filemanager, False)
            self.assertEqual(runmanager, False)

        self.assertEqual(os.path.exists(project_path), False)
        self.assertEqual(exitexception.exception.code, 1)

    def test_init_from_scratch_config_globus(self):
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        pargv = ['--test', '-c',
                 'tests/test_configs/valid_config_from_scratch_globus.cfg']
        project_path = '/p/user_pub/e3sm/baldwin32/testing/empty/'
        if os.path.exists(project_path):
            shutil.rmtree(project_path)

        config, filemanager, runmanager = initialize(
            argv=pargv,
            version=__version__,
            branch=__branch__,
            event_list=EventList())

        self.assertNotEqual(config, False)
        self.assertNotEqual(filemanager, False)
        self.assertNotEqual(runmanager, False)

        self.assertEqual(os.path.exists(project_path), True)
        if os.path.exists(project_path):
            shutil.rmtree(project_path)

    def test_init_from_scratch_config_globus_bad_uuid(self):
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        pargv = ['--test', '-c',
                 'tests/test_configs/valid_config_from_scratch_globus_bad_uuid.cfg']
        project_path = '/p/user_pub/e3sm/baldwin32/testing/empty/'
        if os.path.exists(project_path):
            shutil.rmtree(project_path)

        config, filemanager, runmanager = initialize(
            argv=pargv,
            version=__version__,
            branch=__branch__,
            event_list=EventList())

        self.assertEqual(config, False)
        self.assertEqual(filemanager, False)
        self.assertEqual(runmanager, False)

        self.assertEqual(os.path.exists(project_path), True)
        if os.path.exists(project_path):
            shutil.rmtree(project_path)


if __name__ == '__main__':
    unittest.main()
