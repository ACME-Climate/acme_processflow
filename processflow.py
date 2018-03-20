# pylint: disable=C0103
# pylint: disable=C0111
# pylint: disable=C0301

import sys
import os
import threading
import logging
from time import sleep

from globus_cli.services.transfer import get_client

from lib.events import EventList
from lib.initialize import initialize
from lib.finalize import finalize
from lib.filemanager import FileManager
from lib.runmanager import RunManager
from lib.display import start_display
from lib.util import (print_line,
                      path_exists,
                      write_human_state,
                      print_message,
                      print_debug,
                      transfer_directory)

# check for NCL
if not os.environ.get('NCARG_ROOT'):
    ncar_path = '/usr/local/src/NCL-6.3.0'
    if os.path.exists(ncar_path):
        os.environ['NCARG_ROOT'] = ncar_path
    else:
        print 'No NCARG_ROOT found in environment variables, make sure NCL installed on the machine and add its path to your ~/.bashrc'
        sys.exit()

# set variable to make vcs shut up
os.environ['UVCDAT_ANONYMOUS_LOG'] = 'False'

__version__ = "1.0.1"

# create global EventList
event_list = EventList()

def main(test=False, **kwargs):
    # The master configuration object
    config = {}

    # A list of all the threads
    thread_list = []

    # An event to kill the threads on terminal exception
    thread_kill_event = threading.Event()
    mutex = threading.Lock()
    display_event = threading.Event()

    # A flag to tell if we have all the data locally
    all_data = False
    all_data_remote = False

    # get a globus client
    client = get_client()

    # Read in parameters from config
    args = kwargs['testargs'] if test else sys.argv[1:]
    config, filemanager, runmanager = initialize(
        argv=args,
        event_list=event_list,
        thread_list=thread_list,
        kill_event=thread_kill_event,
        mutex=mutex)

    if isinstance(config, int):
        print "Error in setup, exiting"
        return -1
    logging.info('Config setup complete')
    msg = "Running processflow version {}".format(__version__)
    logging.info(msg)
    print_line(
        ui=config['global']['ui'],
        line=msg,
        event_list=event_list)

    # check that all netCDF files exist
    path_exists(config)
    # cleanup any temp directories from previous runs
    # cleanup(config)
    if not os.path.exists(config['global']['run_scripts_path']):
        os.makedirs(config['global']['run_scripts_path'])
    if not os.path.exists(config['global']['tmp_path']):
        os.makedirs(config['global']['tmp_path'])

    if config['global'].get('ui'):
        try:
            sys.stdout.write('Turning on the display')
            for _ in range(10):
                sys.stdout.write('.')
                sys.stdout.flush()
                sleep(0.1)
            print '\n'
            args = (display_event,
                    runmanager.job_sets,
                    filemanager,
                    event_list)
            diaplay_thread = threading.Thread(
                target=start_display,
                args=args)
            diaplay_thread.start()

        except KeyboardInterrupt as e:
            print 'keyboard interrupt'
            display_event.set()
            return -1

    state_path = os.path.join(
        config.get('global').get('output_path'),
        'run_state.txt')
    msg = "Updating local file status"
    print_line(
        ui=config['global']['ui'],
        line=msg,
        event_list=event_list)
    filemanager.update_local_status()
    all_data = filemanager.all_data_local()
    
    msg = "Writing human readable state to file"
    print_line(
        ui=config['global']['ui'],
        line=msg,
        event_list=event_list,
        current_state=True)
    sleep(0.5)
    write_human_state(
        event_list=event_list,
        job_sets=runmanager.job_sets,
        state_path=state_path,
        print_file_list=config['global'].get('print_file_list'),
        mutex=mutex)
    if not all_data:
        print_line(
            config['global']['ui'],
            "Updating remote file status",
            event_list,
            current_state=False)
        if not config.get('global').get('no_monitor', False):
            filemanager.update_remote_status(client)
            all_data_remote = filemanager.all_data_remote()
        else:
            all_data_remote = True

    # check if the case_scripts directory is present
    # if its not, transfer it over
    if config['global']['no_scripts'] or config['global']['no_monitor']:
        msg = 'Not transfering case_scripts'
        print_line(
            ui=config['global']['ui'],
            line=msg,
            event_list=event_list)
    else:
        msg = 'case_scripts not local, transfering remote copy'
        print_line(
            ui=config['global']['ui'],
            line=msg,
            event_list=event_list)
        case_scripts_dir = os.path.join(
            config['global']['input_path'],
            'case_scripts')

        if not os.path.exists(case_scripts_dir):
            logging.info(msg)
            src_path = os.path.join(
                config['global']['source_path'], 'case_scripts')
            while True:
                try:
                    args = {
                        'source_endpoint': config['transfer']['source_endpoint'],
                        'destination_endpoint': config['transfer']['destination_endpoint'],
                        'src_path': src_path,
                        'dst_path': case_scripts_dir,
                        'event_list': event_list,
                        'event': thread_kill_event
                    }
                    thread = threading.Thread(
                        target=transfer_directory,
                        name='transfer_directory',
                        kwargs=args)
                except:
                    sleep(1)
                else:
                    thread_list.append(thread)
                    thread.start()
                    break

    # Main loop
    remote_check_delay = 60
    local_check_delay = 2
    printed = False
    try:
        loop_count = remote_check_delay - 1
        if not config['global']['ui']:
            print "--------------------------"
            print " Entering Main Loop "
            print " Status file: {}".format(state_path)
            print "--------------------------"
        while True:
            # Check the remote status once every 5 minutes
            if loop_count == remote_check_delay:
                loop_count = 0
                if config.get('global').get('no_monitor', False):
                    loop_count += 1
                    continue
                if not all_data:
                    all_data = filemanager.all_data_local()
                if not all_data_remote and not all_data:
                    all_data_remote = filemanager.all_data_remote()
                if not all_data_remote and not all_data:
                    msg = 'Updating remote status'
                    print_line(
                        ui=config['global']['ui'],
                        line=msg,
                        event_list=event_list,
                        current_state=True)
                    filemanager.update_remote_status(client)
                if not all_data:
                    msg = 'Updating local status'
                    print_line(
                        ui=config['global']['ui'],
                        line=msg,
                        event_list=event_list,
                        current_state=True)
                    filemanager.update_local_status()
            # check the local status every 10 seconds
            if loop_count == local_check_delay:
                if not all_data:
                    all_data = filemanager.all_data_local()
                else:
                    if not printed:
                        msg = 'All data local, turning off remote checks'
                        print_line(
                            ui=config['global']['ui'],
                            line=msg,
                            event_list=event_list)
                        printed = True
                if not all_data \
                        and not config['global']['no_monitor']:
                    transfer_started = filemanager.transfer_needed(
                        event_list=event_list,
                        event=thread_kill_event,
                        remote_endpoint=config['transfer']['source_endpoint'],
                        ui=config['global']['ui'],
                        display_event=display_event,
                        emailaddr=config['global']['email'],
                        thread_list=thread_list)

            msg = "Checking for ready job sets"
            print_line(
                ui=config['global']['ui'],
                line=msg,
                event_list=event_list,
                current_state=True,
                ignore_text=True)
            filemanager.check_year_sets(runmanager.job_sets)
            msg = "Starting ready jobs"
            print_line(
                ui=config['global']['ui'],
                line=msg,
                event_list=event_list,
                current_state=True,
                ignore_text=True)
            sleep(0.5)
            if not runmanager.start_ready_job_sets():
                msg = "Additional data needed"
                print_line(
                    ui=config['global']['ui'],
                    line=msg,
                    event_list=event_list,
                    current_state=True,
                    ignore_text=True)
                filemanager.transfer_needed(
                    event_list=event_list,
                    event=thread_kill_event,
                    remote_endpoint=config['transfer']['source_endpoint'],
                    ui=config['global']['ui'],
                    display_event=display_event,
                    emailaddr=config['global']['email'],
                    thread_list=thread_list)
            msg = "Checking running job status"
            print_line(
                ui=config['global']['ui'],
                line=msg,
                event_list=event_list,
                current_state=True,
                ignore_text=True)
            sleep(0.5)
            runmanager.monitor_running_jobs()
            write_human_state(
                event_list=event_list,
                job_sets=runmanager.job_sets,
                state_path=state_path,
                print_file_list=config.get('global').get('print_file_list'),
                mutex=mutex)
            
            status = runmanager.is_all_done()
            # return -1 if still running
            # return 0 if a jobset failed
            # return 1 if all complete
            if status >= 0:
                first_print = True
                while not filemanager.all_data_local():
                    if first_print:
                        msg = "All jobs complete, moving additional files"
                        print_line(
                            ui=config['global']['ui'],
                            line=msg,
                            event_list=event_list,
                            current_state=True)
                        first_print = False
                    started = filemanager.transfer_needed(
                        event_list=event_list,
                        event=thread_kill_event,
                        remote_endpoint=config['transfer']['source_endpoint'],
                        ui=config['global']['ui'],
                        display_event=display_event,
                        emailaddr=config['global']['email'],
                        thread_list=thread_list)
                    if not started:
                        sleep(5)
                    else:
                        msg = "Transfer started"
                        print_line(
                            ui=config['global']['ui'],
                            line=msg,
                            event_list=event_list)
                msg = "Finishing up run"
                print_line(
                    ui=config['global']['ui'],
                    line=msg,
                    event_list=event_list,
                    current_state=True)
                finalize(
                    config=config,
                    job_sets=runmanager.job_sets,
                    event_list=event_list,
                    status=status,
                    display_event=display_event,
                    thread_list=thread_list,
                    kill_event=thread_kill_event)
                # SUCCESS EXIT
                return 0
            print_line(
                ui=config['global']['ui'],
                line='sleeping',
                event_list=event_list,
                current_state=True,
                ignore_text=True)
            sleep(5)
            loop_count += 1
    except KeyboardInterrupt as e:
        print_message('----- KEYBOARD INTERRUPT -----')
        print_message('----- cleaning up threads ---', 'ok')
        event_list.push(message="Exiting due to keyboard interrupt")
        write_human_state(
            event_list=event_list,
            job_sets=runmanager.job_sets,
            state_path=state_path,
            print_file_list=True,
            mutex=mutex)
        display_event.set()
        thread_kill_event.set()
        for thread in thread_list:
            thread.join(timeout=1.0)
    except Exception as e:
        display_event.set()
        thread_kill_event.set()
        for thread in thread_list:
            thread.join(timeout=1.0)
        sleep(1)
        print_message('----- UNEXPECTED EXCEPTION OCCURED -----')
        print_debug(e)


if __name__ == "__main__":
    if sys.argv[1] == 'test':
        config_path = os.path.join(os.getcwd(), 'tests', 'test_run_no_sta.cfg')
        testargs = ['-c', config_path, '-n', '-f']
        ret = main(test=True, testargs=testargs)
    else:
        ret = main()
    sys.exit(ret)
