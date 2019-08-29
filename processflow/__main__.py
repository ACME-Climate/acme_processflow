#!/usr/bin/env python
from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import os
import sys
import threading

from time import sleep

from processflow.lib.events import EventList
from processflow.lib.finalize import finalize
from processflow.lib.initialize import initialize
from processflow.lib.util import print_debug, print_line, print_message

os.environ['UVCDAT_ANONYMOUS_LOG'] = 'no'
os.environ['NCO_PATH_OVERRIDE'] = 'no'


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

    # Read in parameters from config
    if cl_args is None and len(sys.argv) > 1:
        cl_args = sys.argv[1:]
    elif len(sys.argv) > 1:
        logging.debug("Both command line arguments and programmatic arguments "
                      "are present; defaulting to programmatic arguments.\n"
                      "    programmatic: main({})\n"
                      "    command line: {}".format(cl_args,
                                                    ' '.join(sys.argv[:])))

    config, runmanager = initialize(
        argv=cl_args,
        event_list=event_list)

    if isinstance(config, int):
        print("Error in setup, exiting")
        return -1
    logging.info('Config setup complete')
    debug = True if config['global'].get('debug') else False

    # Main loop
    loop_delay = 10
    state_path = os.path.join(
        config['global']['project_path'],
        'output',
        'job_state.txt')
    try:
        print("--------------------------")
        print(" Entering Main Loop ")
        print(" Status file: {}".format(state_path))
        print("--------------------------")
        while True:

            if debug:
                print_line(' -- checking data -- ', event_list)
            runmanager.check_data_ready()

            if debug:
                print_line(' -- starting ready jobs --', event_list)
            runmanager.start_ready_jobs()

            if debug:
                print_line(' -- monitoring running jobs --', event_list)
            runmanager.monitor_running_jobs(debug=debug)

            if debug:
                print_line(' -- writing out state -- ', event_list)
            runmanager.write_job_sets(state_path)

            status = runmanager.is_all_done()
            if status >= 0:
                msg = "Finishing up run"
                print_line(msg, event_list)
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
        print_message('-----  cleanup complete  -----', 'ok')
    except Exception as e:
        print_message('----- AN UNEXPECTED EXCEPTION OCCURED -----')
        print_debug(e)
        runmanager.write_job_sets(state_path)
# -----------------------------------------------


if __name__ == "__main__":
    sys.exit(main())
# -----------------------------------------------
