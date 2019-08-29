from __future__ import absolute_import, division, print_function, unicode_literals
from time import sleep
from subprocess import Popen, PIPE

from processflow.lib.jobinfo import JobInfo
from processflow.lib.jobstatus import JobStatus


class Serial(object):
    """
    A Python class for submitting one job at a time in serial
    """

    def __init__(self):
        """
        """
        self.status = 'idle'
        self.job_id = 0
        self.jobs = list()
    # -----------------------------------------------

    def batch(self, cmd, pargs=None):
        """
        Submit to the batch queue in non-interactive mode

        Parameters
        ----------
            cmd (str): The path to the run script that should be submitted
            pargs (str): The additional arguments to pass to pbs
        Returns
        -------
            job id of the new job (int)
        """
        if self.status != 'idle':
            return ""

        command = "bash " + cmd

        self.job_id = self.job_id + 1
        self.jobs.append(
            JobInfo(
                jobid=self.job_id,
                command=command,
                state=JobStatus.RUNNING))

        self.status = 'running'
        proc = Popen(command, shell=True, stderr=PIPE, stdout=PIPE)
        while proc.poll() is None:
            sleep(1)

        self.status = 'idle'
        out, err = proc.communicate()
        if err:
            print(err)
        return self.job_id
    # -----------------------------------------------

    def showjob(self, jobid):
        jobs = [job for job in self.jobs if job.job_id == jobid]
        return jobs[0] if jobs else None
    # -----------------------------------------------

    def get_node_number(self, queue='acme'):
        return 1
    # -----------------------------------------------
