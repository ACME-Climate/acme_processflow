#!/usr/bin/env python

import logging
import os
import sys
import threading

from time import sleep

from processflow.lib.events import EventList
from processflow.lib.finalize import finalize
from processflow.lib.initialize import initialize
from processflow.lib.util import print_debug, print_line, print_message


__version__ = '2.2.1'
__branch__ = 'master'

os.environ['UVCDAT_ANONYMOUS_LOG'] = 'no'
os.environ['NCO_PATH_OVERRIDE'] = 'True'


def main(cl_args=None):
    """
    Processflow main

    Parameters:
        test (bool): turns on test mode. Simply stops the logger from reloading itself, which
            stops a crash when running from inside the test runner
        kwargs (dict): when running in test mode, arguments are passed directly through the kwargs
            which bypasses the argument parsing.
    """
    # create global EventList
    event_list = EventList()

    # The master configuration object
    config = {}

    # An event to kill the threads on terminal exception
    thread_kill_event = threading.Event()

    # A flag to tell if we have all the data locally
    all_data_local = False

    # Read in parameters from config
    if cl_args is None and len(sys.argv) > 1:
        cl_args = sys.argv[1:]
    elif len(sys.argv) > 1:
        logging.debug("Both command line arguments and programmatic arguments "
                      "are present; defaulting to programmatic arguments.\n"
                      "    programmatic: main({})\n"
                      "    command line: {}".format(cl_args,
                                                    ' '.join(sys.argv[:])))

    config, filemanager, runmanager = initialize(
        argv=cl_args,
        version=__version__,
        branch=__branch__,
        event_list=event_list,
        kill_event=thread_kill_event)

    if isinstance(config, int):
        print "Error in setup, exiting"
        return -1
    logging.info('Config setup complete')
    debug = True if config['global'].get('debug') else False

    if config['global'].get('no_check'):
        all_data_local = True
    else:
        msg = "Updating local file status"
        print_line(
            line=msg,
            event_list=event_list)
        filemanager.update_local_status()
        all_data_local = filemanager.all_data_local()

        if not all_data_local:
            transfer_status = filemanager.transfer_needed(
                event_list=event_list,
                event=thread_kill_event,
                config=config)
            if transfer_status == False:
                sys.exit(1)

    # Main loop
    printed = False
    loop_delay = 10
    state_path = os.path.join(
        config['global']['project_path'],
        'output',
        'job_state.txt')
    try:
        print "--------------------------"
        print " Entering Main Loop "
        print " Status file: {}".format(state_path)
        print "--------------------------"
        while True:
            if not all_data_local:
                if debug:
                    print_line(' -- Updating local status --', event_list)

                if filemanager.update_local_status():
                    msg = filemanager.report_files_local()
                    print_line(msg, event_list)
                    filemanager.write_database()
                all_data_local = filemanager.all_data_local()
            if not all_data_local:
                if debug:
                    print_line(' -- Additional data needed --', event_list)
                transfer_status = filemanager.transfer_needed(
                    event_list=event_list,
                    event=thread_kill_event,
                    config=config)
                if transfer_status == False:
                    sys.exit(1)

            if debug:
                print_line(' -- checking data -- ', event_list)
            runmanager.check_data_ready()
            if debug:
                print_line(' -- starting ready jobs --', event_list)
            runmanager.start_ready_jobs()
            if debug:
                print_line(' -- monitoring running jobs --', event_list)
            runmanager.monitor_running_jobs()

            if debug:
                print_line(' -- writing out state -- ', event_list)
            runmanager.write_job_sets(state_path)

            status = runmanager.is_all_done()
            # return -1 if still running
            # return 0 if a jobset failed
            # return 1 if all complete
            if status >= 0:
                msg = "Finishing up run"
                print_line(msg, event_list)

                printed = False
                while not filemanager.all_data_local():
                    if not printed:
                        printed = True
                        msg = 'Jobs are complete, but additional data is being transfered'
                        print_line(msg, event_list)
                    filemanager.update_local_status()
                    if not filemanager.all_data_local():
                        transfer_status = filemanager.transfer_needed(
                            event_list=event_list,
                            event=thread_kill_event,
                            config=config)
                        if transfer_status == False:
                            sys.exit(1)
                    sleep(10)
                filemanager.write_database()
                finalize(
                    config=config,
                    event_list=event_list,
                    status=status,
                    runmanager=runmanager)
                # SUCCESS EXIT
                return 0
            if debug:
                print_line(' -- sleeping', event_list)
            sleep(loop_delay)
    except KeyboardInterrupt as e:
        print_message('\n----- KEYBOARD INTERRUPT -----')
        runmanager.write_job_sets(state_path)
        filemanager.terminate_transfers()
        print_message('-----  cleanup complete  -----', 'ok')
    except Exception as e:
        print_message('----- AN UNEXPECTED EXCEPTION OCCURED -----')
        print_debug(e)
        runmanager.write_job_sets(state_path)
        filemanager.terminate_transfers()


if __name__ == "__main__":
    sys.exit(main())
