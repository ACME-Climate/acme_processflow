import sys
import os
import logging
import json
import time
import stat
import argparse

from pprint import pformat
from shutil import rmtree, copy

from configobj import ConfigObj
from YearSet import YearSet, SetStatus
from shutil import copyfile
from lib.filemanager import FileManager
from lib.runmanager import RunManager
from lib.mailer import Mailer
from jobs.JobStatus import JobStatus
from util import (setup_globus,
                  check_globus,
                  print_message,
                  print_debug,
                  print_line)


def parse_args(argv=None, print_help=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c',
        '--config',
        help='Path to configuration file.')
    parser.add_argument(
        '-v',
        '--version',
        help='Print version informat and exit.',
        action='store_true')
    parser.add_argument(
        '-u',
        '--ui',
        help='Turn on the GUI.',
        action='store_true')
    parser.add_argument(
        '-l',
        '--log',
        help='Path to logging output file.')
    parser.add_argument(
        '-n',
        '--no-host',
        help='Don\'t move output plots into the web host directory.',
        action='store_true')
    parser.add_argument(
        '-m',
        '--no-monitor',
        help='Don\'t run the remote monitor or move any files over globus.',
        action='store_true')
    parser.add_argument(
        '-s',
        '--no-scripts',
        help='Don\'t copy the case_scripts directory from the remote machine.',
        action='store_true')
    parser.add_argument(
        '-f',
        '--file-list',
        help='Turn on debug output of the internal file_list so you can see what the current state of the model files are',
        action='store_true')
    parser.add_argument(
        '-r',
        '--resource-dir',
        help='Path to custom resource directory')
    parser.add_argument(
        '-i',
        '--input-path',
        help='Custom input path')
    parser.add_argument(
        '-o',
        '--output-path',
        help='Custom output path')
    parser.add_argument(
        '-a',
        '--always-copy',
        help='Always copy diagnostic output, even if the output already exists in the host directory. This is much slower but ensures old output will be overwritten',
        action='store_true')
    if print_help:
        parser.print_help()
        return
    return parser.parse_args(argv)


def initialize(argv, **kwargs):
    """
    Parse the commandline arguments, and setup the master config dict

    Parameters:
        parser (argparse.ArgumentParser): The parser object
        event_list (EventList): The main list of events
        thread_list (list): the main list of all running threads
        mutex (threading.Lock): A mutex to handle db access
        kill_event (threading.Event): An event used to kill all running threads
        version (str): the current version number for processflow
        branch (str): the branch this version was built from
    """
    # Setup the parser
    args = parse_args(argv=argv)
    if args.version:
        msg = 'Processflow version {}'.format(kwargs['version'])
        print msg
        sys.exit()
    if not args.config:
        parse_args(print_help=True)
        return False, False, False
    event_list = kwargs['event_list']
    thread_list = kwargs['thread_list']
    mutex = kwargs['mutex']
    event = kwargs['kill_event']
    print_line(
        ui=False,
        line='Entering setup',
        event_list=event_list,
        current_state=True)

    # check if globus config is valid, else remove it
    globus_config = os.path.join(os.path.expanduser('~'), '.globus.cfg')
    if os.path.exists(globus_config):
        try:
            conf = ConfigObj(globus_config)
        except:
            os.remove(globus_config)

    if not os.path.exists(args.config):
        print "Invalid config, {} does not exist".format(args.config)
        return False, False, False

    # Check that there are no white space errors in the config file
    line_index = check_config_white_space(args.config)
    if line_index != 0:
        print '''
ERROR: line {num} does not have a space after the \'=\', white space is required.
Please add a space and run again.'''.format(num=line_index)
        return False, False, False

    # read the config file and setup the config dict
    try:
        config = ConfigObj(args.config)
    except Exception as e:
        print "Error parsing config file {}".format(args.config)
        parse_args(print_help=True)
        return False, False, False

    # run validator for config file
    if config.get('global'):
        if args.resource_dir:
            config['global']['resource_dir'] = args.resource_dir
        else:
            config['global']['resource_dir'] = os.path.join(
                sys.prefix,
                'share',
                'processflow',
                'resources')
    else:
        return False, False, False

    # Setup boolean config flags
    config['global']['ui'] = True if args.ui else False
    config['global']['no_host'] = True if args.no_host else False
    config['global']['no_monitor'] = True if args.no_monitor else False
    config['global']['print_file_list'] = True if args.file_list else False
    config['global']['no_scripts'] = True if args.no_scripts else False
    config['global']['always_copy'] = True if args.always_copy else False

    if args.no_host:
        print_line(
        ui=False,
        line='Not hosting web output',
        event_list=event_list,
        current_state=True)

    template_path = os.path.join(
        config['global']['resource_dir'],
        'config_template.json')

    with open(template_path, 'r') as template_file:
        template = json.load(template_file)

    valid, messages = verify_config(config, template)
    if not valid:
        for message in messages:
            print message
        return False, False, False

    if args.input_path:
        config['global']['input_path'] = args.input_path
    else:
        config['global']['input_path'] = os.path.join(
            config['global']['project_path'],
            'input')
    if args.output_path:
        config['global']['output_path'] = args.output_path
    else:
        config['global']['output_path'] = os.path.join(
            config['global']['project_path'],
            'output')

    # setup output and cache directories
    if not os.path.exists(config['global']['input_path']):
        os.makedirs(config['global']['input_path'])
    if not os.path.exists(config['global']['output_path']):
        os.makedirs(config['global']['output_path'])

    pp_path = os.path.join(config['global']['output_path'], 'pp')
    if not os.path.exists(pp_path):
        os.makedirs(pp_path)
    diags_path = os.path.join(config['global']['output_path'], 'diags')
    if not os.path.exists(diags_path):
        os.makedirs(diags_path)
    config['global']['pp_path'] = pp_path
    config['global']['diags_path'] = diags_path

    # check if account information is given
    if not config['global'].get('account'):
        config['global']['account'] = ''

    # Copy the config into the input directory for safe keeping
    input_config_path = os.path.join(
        config['global']['input_path'], 'run.cfg')
    try:
        copy(args.config, input_config_path)
    except:
        pass

    # setup logging
    if args.log:
        log_path = args.log
    else:
        log_path = os.path.join(
            config.get('global').get('output_path'),
            'processflow.log')
    print_line(
        ui=config['global']['ui'],
        line='Log saved to {}'.format(log_path),
        event_list=event_list,
        current_state=True)
    from imp import reload
    reload(logging)
    config['global']['log_path'] = log_path
    logging.basicConfig(
        format='%(asctime)s:%(levelname)s: %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p',
        filename=log_path,
        filemode='w',
        level=logging.DEBUG)
    logging.getLogger('globus_sdk').setLevel(logging.ERROR)
    logging.getLogger('globus_cli').setLevel(logging.ERROR)

    msg = 'processflow version {} branch {}'.format(
        kwargs['version'],
        kwargs['branch'])
    logging.info(msg)

    if config['global']['always_copy']:
        msg = 'Running in forced-copy mode, all previous diagnostic output will be overwritten'
    else:
        msg = 'Running without forced-copy, previous diagnostic output will be preserved'
    print_line(
            ui=config['global']['ui'],
            line=msg,
            event_list=event_list,
            current_state=True)

    # Make sure the set_frequency is a list of ints
    set_frequency = config['global']['set_frequency']
    if not isinstance(set_frequency, list):
        set_frequency = [int(set_frequency)]
    else:
        # These are sometimes strings which break things later
        new_freqs = []
        for freq in set_frequency:
            new_freqs.append(int(freq))
        set_frequency = new_freqs
    config['global']['set_frequency'] = set_frequency

    # setup config for file type directories
    if not isinstance(config['global']['file_types'], list):
        config['global']['file_types'] = [config['global']['file_types']]

    # setup run_scipts_path
    run_script_path = os.path.join(
        config['global']['output_path'],
        'run_scripts')
    config['global']['run_scripts_path'] = run_script_path
    if not os.path.exists(run_script_path):
        os.makedirs(run_script_path)

    # setup tmp_path
    tmp_path = os.path.join(
        config['global']['output_path'],
        'tmp')
    config['global']['tmp_path'] = tmp_path
    if os.path.exists(tmp_path):
        rmtree(tmp_path)
    os.makedirs(tmp_path)

    # setup the year_set list
    config['global']['simulation_start_year'] = int(
        config['global']['simulation_start_year'])
    config['global']['simulation_end_year'] = int(
        config['global']['simulation_end_year'])
    sim_start_year = int(config['global']['simulation_start_year'])
    sim_end_year = int(config['global']['simulation_end_year'])

    config['global']['short_term_archive'] = int(
        config['global']['short_term_archive'])

    # initialize the filemanager
    event_list.push(message='Initializing file manager')
    head, tail = os.path.split(config['global']['source_path'])
    if tail == 'run':
        config['global']['source_path'] = head

    db_path = os.path.join(config['global']['input_path'], 'processflow.db')
    if not os.path.exists(config['global']['input_path']):
        os.makedirs(config['global']['input_path'])

    filemanager = FileManager(
        event_list=event_list,
        ui=config['global']['ui'],
        database=db_path,
        types=config['global']['file_types'],
        sta=config['global']['short_term_archive'],
        remote_path=config['global']['source_path'],
        remote_endpoint=config['transfer']['source_endpoint'],
        local_path=config['global']['input_path'],
        local_endpoint=config['transfer']['destination_endpoint'],
        mutex=mutex)
    filemanager.populate_file_list(
        simstart=config['global']['simulation_start_year'],
        simend=config['global']['simulation_end_year'],
        experiment=config['global']['experiment'])
    print_line(
        ui=config['global']['ui'],
        line='Updating local status',
        event_list=event_list,
        current_state=True)
    filemanager.update_local_status()
    print_line(
        ui=config['global']['ui'],
        line='Local status update complete',
        event_list=event_list,
        current_state=True)
    all_data = filemanager.all_data_local()
    if all_data:
        line = 'All data is local'
    else:
        line = 'Additional data needed'
    print_line(
        ui=config['global']['ui'],
        line=line,
        event_list=event_list,
        current_state=True)

    logging.info("FileManager setup complete")
    logging.info(str(filemanager))

    if all_data or args.no_monitor:
        print_line(
            ui=config['global']['ui'],
            line="skipping globus setup",
            event_list=event_list,
            current_state=True)
    else:
        endpoints = [endpoint for endpoint in config['transfer'].values()]
        addr = config.get('global').get('email')
        if not addr:
            print 'When running in text mode, you must enter an email address.'
            return False, False, False
        setup_success = setup_globus(
            endpoints=endpoints,
            ui=False,
            src=config.get('global').get('email'),
            dst=config.get('global').get('email'),
            event_list=event_list)

        if not setup_success:
            print "Globus setup error"
            return False, False, False
        else:
            print_line(
                ui=config['global']['ui'],
                line='Globus authentication complete',
                event_list=event_list,
                current_state=True)

        line = 'Checking file access on globus transfer nodes'
        print_line(
            ui=config['global']['ui'],
            line=line,
            event_list=event_list,
            current_state=True)
        setup_success, endpoint = check_globus(
            source_endpoint=config['transfer']['source_endpoint'],
            source_path=config['global']['source_path'],
            destination_endpoint=config['transfer']['destination_endpoint'],
            destination_path=config['global']['input_path'])
        if not setup_success:
            print 'ERROR! Unable to access {} globus node'.format(endpoint['type'])
            print 'The node may be down, or you may not have access to the requested directory'
            return False, False, False

    # setup the runmanager
    runmanager = RunManager(
        short_name=config['global']['short_name'],
        account=config['global']['account'],
        resource_path=config['global']['resource_dir'],
        ui=config['global']['ui'],
        event_list=event_list,
        output_path=config['global']['output_path'],
        caseID=config['global']['experiment'],
        scripts_path=run_script_path,
        thread_list=thread_list,
        event=event,
        no_host=config['global']['no_host'],
        url_prefix=config['global']['url_prefix'],
        always_copy=config['global']['always_copy'])
    runmanager.setup_job_sets(
        set_frequency=config['global']['set_frequency'],
        sim_start_year=sim_start_year,
        sim_end_year=sim_end_year,
        config=config,
        filemanager=filemanager)

    logging.info('Starting run with config:')
    logging.info(json.dumps(config, indent=4, sort_keys=True))
    return config, filemanager, runmanager


def verify_config(config, template):
    messages = []
    valid = True
    for key, val in template.items():
        if key not in config:
            msg = '{key} is missing from your config'.format(key=key)
            messages.append(msg)
            valid = False
        for item in val:
            if not config.get(key):
                msg = '{key} requires {val} but it is missing from your config'.format(
                    key=key, val=item)
                messages.append(msg)
                valid = False
                continue
            if item not in config[key]:
                msg = '{key} requires {val} but it is missing from your config'.format(
                    key=key, val=item)
                messages.append(msg)
                valid = False
    return valid, messages


def check_config_white_space(filepath):
    line_index = 0
    found = False
    with open(filepath, 'r') as infile:
        for line in infile.readlines():
            line_index += 1
            index = line.find('=')
            if index == -1:
                found = False
                continue
            if line[index + 1] != ' ':
                found = True
                break
    if found:
        return line_index
    else:
        return 0
