import os
import logging
import time

from jobs.JobStatus import JobStatus, StatusMap, ReverseMap
from lib.mailer import Mailer
from lib.util import print_message, print_line, print_debug, native_cleanup


def finalize(config, job_sets, event_list, status, display_event, thread_list, kill_event, runmanager):
    if status == 1 and config['global']['native_grid_cleanup'] in [1, '1', 'true']:
        message = 'Performing post run cleanup'
        native_cleanup(
            output_path=config['global']['output_path'],
            native_grid_name=config['global']['native_grid_name'])
    else:
        message = 'Leaving native grid files in place'

    print_line(
            ui=config['global']['ui'],
            line=message,
            event_list=event_list,
            current_state=True,
            ignore_text=False)

    message = 'All processing complete' if status == 1 else "One or more job failed"
    emailaddr = config.get('global').get('email')
    if emailaddr:
        event_list.push(
            message='Sending notification email to {}'.format(emailaddr))
        try:
            if status == 1:
                msg = 'Post processing for {exp} has completed successfully\n'.format(
                    exp=config['global']['experiment'])
            else:
                msg = 'One or more job(s) for {exp} failed\n\n'.format(
                    exp=config['global']['experiment'])

            for job_set in job_sets:
                if not job_set.jobs:
                    continue
                msg += '\nYearSet {start}-{end}: {status}\n'.format(
                    start=job_set.set_start_year,
                    end=job_set.set_end_year,
                    status=job_set.status)
                for job in job_set.jobs:
                    if job.status == JobStatus.COMPLETED:
                        if job.config.get('host_url'):
                            url = runmanager._format_url(job)
                            msg += '    > {job} - COMPLETED  :: output hosted :: {url}\n'.format(
                                url=url,
                                job=job.type)
                        else:
                            msg += '    > {job} - COMPLETED  :: output located :: {output}\n'.format(
                                output=job.output_path,
                                job=job.type)
                    elif job.status in [JobStatus.FAILED, JobStatus.CANCELLED]:
                        output_path = os.path.join(
                            job.config['run_scripts_path'],
                            '{job}_{start:04d}_{end:04d}.out'.format(
                                job=job.type,
                                start=job.start_year,
                                end=job.end_year))
                        msg += '    > {job} - {status} :: console output :: {output}\n'.format(
                            output=output_path,
                            job=job.type,
                            status=ReverseMap[job.status])
                    else:
                        msg += '    > {job} - {state}\n'.format(
                            job=job.type,
                            state=ReverseMap[job.status])
                msg += '\n\n'

            m = Mailer(src='processflowbot@llnl.gov', dst=emailaddr)
            m.send(
                status=message,
                msg=msg)
        except Exception as e:
            print_debug(e)
    event_list.push(message=message)
    display_event.set()
    print_type = 'ok' if status == 1 else 'error'
    print_message(message, print_type)
    logging.info("All processes complete")
    kill_event.set()
    for t in thread_list:
        t.join(timeout=1.0)
    time.sleep(2)

