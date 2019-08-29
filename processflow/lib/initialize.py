from __future__ import absolute_import, division, print_function, unicode_literals
import argparse
import json
import logging
import os
import sys

from shutil import copy
from shutil import copyfile

from configobj import ConfigObj

from processflow import resources
from processflow.lib.filemanager import FileManager
from processflow.lib.runmanager import RunManager
from processflow.lib.util import print_debug
from processflow.lib.util import print_line
from processflow.lib.util import print_message
from processflow.lib.verify_config import verify_config, check_config_white_space
from processflow.version import __version__, __branch__


def parse_args(argv=None, print_help=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'config',
        nargs='?',
        help='Path to configuration file.')
    parser.add_argument(
        '-m', '--max-jobs',
        help='Maximum number of jobs to run at any given time',
        type=int)
    parser.add_argument(
        '-l', '--log',
        help='Path to logging output file, defaults to project_path/output/processflow.log')
    parser.add_argument(
        '-a', '--always-copy',
        help='Always copy diagnostic output, even if the output already exists in the host directory. This is much slower but ensures old output will be overwritten',
        action='store_true')
    parser.add_argument(
        '-r', '--resource-path',
        help='Path to custom resource directory')
    parser.add_argument(
        '--debug',
        help='Set log level to debug',
        action='store_true')
    parser.add_argument(
        '--dryrun',
        help='Do everything up to starting the jobs, but dont start any jobs',
        action='store_true')
    parser.add_argument(
        '-v', '--version',
        help='Print version information and exit.',
        action='store_true')
    parser.add_argument(
        '-s', '--serial',
        help="Run in serial on systems without a resource manager",
        action='store_true')
    parser.add_argument(
        '--test',
        help=argparse.SUPPRESS,
        action='store_true')
    if print_help:
        parser.print_help()
        return
    return parser.parse_args(argv)
# -----------------------------------------------


def initialize(argv, **kwargs):
    """
    Parse the commandline arguments, and setup the master config dict

    Parameters:
        argv (list): a list of arguments
        event_list (EventList): The main list of events
        __version__ (str): the current version number for processflow
        __branch__ (str): the branch this version was built from
    """
    if argv and '--test' in argv:
        print('==========================================')
        print('---- Processflow running in test mode ----')
        print('==========================================')
    # Setup the parser
    pargs = parse_args(argv=argv)
    if pargs.version:
        print(('Processflow version {} from branch {}'.format(
            __version__, __branch__)))
        sys.exit(0)
    if not pargs.config:
        parse_args(print_help=True)
        return False, False, False
    if not os.path.isfile(pargs.config):
        msg = "The referenced config is not a regular file, please select a config file"
        print_message(msg)
        return False, False, False
    event_list = kwargs['event_list']
    print_line(
        line='Entering setup',
        event_list=event_list)

    if not os.path.exists(pargs.config):
        print("Invalid config, {} does not exist".format(pargs.config))
        return False, False, False

    # Check that there are no white space errors in the config file
    line_index = check_config_white_space(pargs.config)
    if line_index != 0:
        print('''
ERROR: line {num} does not have a space after the \'=\', white space is required.
Please add a space and run again.'''.format(num=line_index))
        return False, False, False

    # read the config file and setup the config dict
    try:
        config = ConfigObj(pargs.config)
    except Exception as e:
        print_debug(e)
        print("Error parsing config file {}".format(pargs.config))
        parse_args(print_help=True)
        return False, False, False

    # run validator for config file
    messages = verify_config(config)
    if messages:
        for message in messages:
            print_message(message)
        return False, False

    try:
        setup_directories(config)
    except Exception as e:
        print_message('Failed to setup directories')
        print_debug(e)
        sys.exit(1)

    if pargs.resource_path:
        config['global']['resource_path'] = os.path.abspath(
            pargs.resource_path)
    else:
        config['global']['resource_path'] = os.path.dirname(resources.__file__)

    # Setup boolean config flags
    config['global']['host'] = True if config.get('img_hosting') else False
    config['global']['always_copy'] = True if pargs.always_copy else False
    config['global']['dryrun'] = True if pargs.dryrun else False
    config['global']['debug'] = True if pargs.debug else False
    config['global']['max_jobs'] = pargs.max_jobs if pargs.max_jobs else False
    config['global']['serial'] = True if pargs.serial else False

    # setup logging
    if pargs.log:
        log_path = pargs.log
    else:
        log_path = os.path.join(
            config['global']['project_path'],
            'output',
            'processflow.log')
    print_line(
        line='Log saved to {}'.format(log_path),
        event_list=event_list)

    config['global']['log_path'] = log_path
    if os.path.exists(log_path):
        logbak = log_path + '.bak'
        if os.path.exists(logbak):
            os.remove(logbak)
        copyfile(log_path, log_path + '.bak')
    log_level = logging.DEBUG if pargs.debug else logging.INFO
    logging.basicConfig(
        format='%(asctime)s:%(levelname)s: %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p',
        filename=log_path,
        filemode='w',
        level=log_level)

    logging.info("Running with config:")
    msg = json.dumps(config, sort_keys=False, indent=4)
    logging.info(msg)

    if pargs.max_jobs:
        print_line(
            line="running with maximum {} jobs".format(pargs.max_jobs),
            event_list=event_list)

    if not config['global']['host'] or not config.get('img_hosting'):
        print_line(
            line='Not hosting img output',
            event_list=event_list)

    msg = 'processflow version {} branch {}'.format(
        __version__,
        __branch__)
    logging.info(msg)

    # Copy the config into the input directory for safe keeping
    # if there's already a version there, then remove it and 
    # copy in the new version
    input_config_path = os.path.join(
        config['global']['project_path'],
        'run.cfg')
    # if we're using the config in the project directory no need to copy
    if pargs.config != input_config_path:
        if os.path.exists(input_config_path):
            os.remove(input_config_path)
        copy(pargs.config, input_config_path)

    if config['global']['always_copy']:
        msg = 'Running in forced-copy mode, previously hosted diagnostic output will be replaced'
    else:
        msg = 'Running without forced-copy, previous hosted output will be preserved'
    print_line(
        line=msg,
        event_list=event_list)

    # initialize the filemanager
    db = os.path.join(
        config['global'].get('project_path'),
        'output',
        'processflow.db')
    msg = 'Initializing file manager'
    print_line(msg, event_list)
    filemanager = FileManager(
        database=db,
        event_list=event_list,
        config=config)

    filemanager.populate_file_list()

    msg = 'Starting local status update'
    print_line(msg, event_list)

    filemanager.file_status_check()
    msg = 'Local status update complete'
    print_line(msg, event_list)

    all_data = filemanager.all_data_local()

    if all_data:
        msg = 'all data is local'
        print_line(msg, event_list)
    else:
        msg = 'Additional data needed'
        print_message(msg, 'error')
        sys.exit(1)

    logging.info("FileManager setup complete")
    logging.info(str(filemanager))

    # setup the runmanager
    runmanager = RunManager(
        event_list=event_list,
        config=config,
        filemanager=filemanager)

    if pargs.debug:
        msg = '-- setting up cases -- '
        print_line(msg, event_list)
    runmanager.setup_cases()

    if pargs.debug:
        msg = '-- setting up jobs --'
        print_line(msg, event_list)
    runmanager.setup_jobs()

    if pargs.debug:
        msg = '-- writing job state out to file --'
        print_line(msg, event_list)
    runmanager.write_job_sets(
        os.path.join(config['global']['project_path'],
                     'output',
                     'job_state.txt'))
    return config, runmanager
# -----------------------------------------------


def setup_directories(config):
    """
    Setup the input, output, pp, and diags directories
    """
    # setup output directory
    output_path = os.path.join(
        config['global']['project_path'],
        'output')
    config['global']['output_path'] = output_path
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # setup post processing dir
    pp_path = os.path.join(output_path, 'pp')
    config['global']['pp_path'] = pp_path
    if not os.path.exists(pp_path):
        os.makedirs(pp_path)

    # setup diags dir
    diags_path = os.path.join(output_path, 'diags')
    config['global']['diags_path'] = diags_path
    if not os.path.exists(diags_path):
        os.makedirs(diags_path)

    # setup run_scripts_path
    run_script_path = os.path.join(
        output_path,
        'scripts')
    config['global']['run_scripts_path'] = run_script_path
    if not os.path.exists(run_script_path):
        os.makedirs(run_script_path)
# -----------------------------------------------
