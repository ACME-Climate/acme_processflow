from __future__ import absolute_import, division, print_function, unicode_literals
import logging
import os
from shutil import rmtree

from processflow.lib.jobstatus import JobStatus
from processflow.lib.mailer import Mailer
from processflow.lib.util import print_message, print_debug


def finalize(config, event_list, status, runmanager):

    if status == 1:
        msg = 'All processing complete'
        code = 'ok'
    else:
        msg = 'The following jobs encountered an error and were marked as failed:'
        code = 'error'
        for case in runmanager.cases:
            for job in case['jobs']:
                if job.status != JobStatus.COMPLETED:
                    msg += '\n        {}'.format(job.msg_prefix())
    print_message(msg, code)
    emailaddr = config['global'].get('email')
    if emailaddr:
        message = 'Sending notification email to {}'.format(emailaddr)
        print_message(message, 'ok')
        try:
            if status == 1:
                msg = 'Your processflow run has completed successfully\n'
                status = msg
            else:
                msg = 'One or more processflow jobs failed\n'
                status = msg
                msg += 'See log for additional details\n{}\n'.format(
                    config['global']['log_path'])

            for case in runmanager.cases:
                msg += '==' + '='*len(case['case']) + '==\n'
                msg += ' # ' + case['case'] + ' #\n'
                msg += '==' + '='*len(case['case']) + '==\n\n'
                for job in case['jobs']:
                    msg += '\t > ' + job.get_report_string() + '\n'
                msg += '\n'

            m = Mailer(src='processflowbot@llnl.gov', dst=emailaddr)
            m.send(
                status=status,
                msg=msg)
        except Exception as e:
            print_debug(e)

    logging.info("All processes complete")
# -----------------------------------------------
