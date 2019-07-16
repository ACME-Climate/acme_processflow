import logging
import os

from subprocess import Popen, PIPE

from processflow.lib.jobinfo import JobInfo


class PBS(object):
    """
    A Python class for interfacing with the PBS/TORQUE resource management system
    """

    def __init__(self):
        """
        Check if the system has PBS available, raise an exception if it cant be found
        """
        if not any(os.access(os.path.join(path, 'qstat'), os.X_OK) for path in os.environ["PATH"].split(os.pathsep)):
            raise Exception(
                'Unable to find qstat, is PBS installed on this sytem?')
    
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
        command = ['qsub', cmd, pargs] if pargs is not None else ['qsub', cmd]
        proc = Popen(command, shell=False, stderr=PIPE, stdout=PIPE)
        out, err = proc.communicate()
        if err:
            logging.error(err)
        else:
            return out.rstrip()
    
    def showjob(self, jobid):
        """
        A wrapper around 'qstat -f JOBID' to get job info

        Parameters
        ----------
            jobid (str): the job id to get information about
        Returns
        -------
            A jobinfo object holding information about the job
        """
        cmd = ['qstat', '-f', jobid]
        proc = Popen(cmd, shell=False, stderr=PIPE, stdout=PIPE)
        out, err = proc.communicate()
        if err:
            logging.error(err)
        job_info = JobInfo()
        for idx, item in enumerate(out.split('\n')):
            if idx == 0:
                index = item.find(':')
            else:
                index = item.find('=')
                if index <= 0:
                    continue
            attr = item[:index].strip()
            attr = self.pbs_to_jobinfo(attr)
            if attr is None:
                continue
            job_info.set_attr(
                attr=attr.strip(),
                val=item[index + 1:].strip())
        if job_info.state is None:
            raise Exception("No job found with id {}".format(jobid))
        return job_info
    
    def pbs_to_jobinfo(self, attr):
        if attr == 'queue':
            return 'PARTITION'
        elif attr == 'Job_Owner':
            return 'USER'
        elif attr == 'Job_Name':
            return 'NAME'
        elif attr == 'job_state':
            return 'STATE'
        elif attr == 'Job Id':
            return 'JOBID'
        else:
            return None


    def get_node_number(self, queue='acme'):
        """
        Return the number of nodes available in the requested queue

        Parameters
        ----------
            queue (str): the queue to check, defaults to 'acme'
        Returns
        -------
            (int): the number of nodes available to the resource manager
        """
        cmd = ['pbsnodes -a | grep "properties = {}" | wc -l'.format(queue)]
        proc = Popen(cmd, shell=True, stderr=PIPE, stdout=PIPE)
        out, err = proc.communicate()
        if err:
            logging.error(err)
        return int(out.strip())
