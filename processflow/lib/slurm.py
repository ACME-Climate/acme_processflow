from __future__ import absolute_import, division, print_function, unicode_literals
import logging
import os

from subprocess import Popen, PIPE
from time import sleep

from processflow.lib.jobinfo import JobInfo
from processflow.lib.util import print_debug


class Slurm(object):
    """
    A python interface for slurm using subprocesses
    """

    def __init__(self):
        """
        Check if the system has Slurm installed
        """
        if not any(os.access(os.path.join(path, 'sinfo'), os.X_OK) for path in os.environ["PATH"].split(os.pathsep)):
            raise Exception(
                'Unable to find slurm, is it installed on this sytem?')
    # -----------------------------------------------

    def batch(self, cmd, sargs=None):
        """
        Submit to the batch queue in non-interactive mode

        Parameters:
            cmd (str): The path to the run script that should be submitted
            sargs (str): The additional arguments to pass to slurm
        Returns:
            job id of the new job (int)
        """
        try:
            out, err = self._submit('sbatch', cmd, sargs)
        except Exception as e:
            print('Batch job submission failed')
            print_debug(e)
            return 0

        if err:
            raise Exception('SLURM ERROR: ' + err)

        out = out.split()
        if 'error' in out:
            return 0
        try:
            job_id = int(out[-1])
        except IndexError as e:
            print("error submitting job to slurm " + str(out) + " " + str(err))
            return 0

        return job_id
    # -----------------------------------------------

    def _submit(self, subtype, cmd, sargs=None):

        cmd = [subtype, cmd, sargs] if sargs is not None else [subtype, cmd]
        tries = 0
        while tries != 10:
            proc = Popen(cmd, shell=False, stderr=PIPE, stdout=PIPE)
            out, err = proc.communicate()
            if err:
                logging.error(err)
                tries += 1
                sleep(tries * 2)
            if err:
                print(err)
                qinfo = self.queue()
                for job in qinfo:
                    if job.get('COMMAND') == cmd[1]:
                        return 'Submitted batch job {}'.format(job['JOBID']), None
                print('Unable to submit job, trying again')
            else:
                break
        if tries >= 10:
            raise Exception('SLURM ERROR: Transport endpoint is not connected')
        return out, None
    # -----------------------------------------------

    def showjob(self, jobid):
        """
        A wrapper around scontrol show job

        Parameters:
            jobid (str): the job id to get information about
        Returns:
            A jobinfo object containing information about the job with the given jobid
        """
        if not isinstance(jobid, str):
            jobid = str(jobid)
        success = False
        while not success:
            try:
                proc = Popen(['scontrol', 'show', 'job', jobid],
                             shell=False, stderr=PIPE, stdout=PIPE)
                out, err = proc.communicate()
                if err:
                    sleep(1)
                else:
                    success = True
            except:
                success = False
                sleep(1)

        if err:
            raise Exception('SLURM ERROR: ' + err)
        job_info = JobInfo()
        for item in out.split(b'\n'):
            for j in item.split(b' '):
                index = j.find(b'=')
                if index <= 0:
                    continue
                attribute = self.slurm_to_jobinfo(j[:index])
                if attribute is None:
                    continue
                job_info.set_attr(
                    attr=attribute,
                    val=j[index + 1:].decode("utf-8"))
        return job_info
    # -----------------------------------------------

    def slurm_to_jobinfo(self, attr):
        if attr == b'Partition':
            return 'PARTITION'
        elif attr == b'Command':
            return 'COMMAND'
        elif attr == b'UserId':
            return 'USER'
        elif attr == b'JobName':
            return 'NAME'
        elif attr == b'JobState':
            return 'STATE'
        elif attr == b'JobId':
            return 'JOBID'
        elif attr == b'RunTime':
            return 'RUNTIME'
        else:
            return None
    # -----------------------------------------------

    def get_node_number(self):
        """
        Use sinfo to return the number of nodes in the cluster
        """
        cmd = 'sinfo show nodes | grep up | wc -l'
        p = Popen([cmd], stderr=PIPE, stdout=PIPE, shell=True)
        out, err = p.communicate()
        try:
            num_nodes = int(out)
        except:
            num_nodes = 1
        return num_nodes
    # -----------------------------------------------

    def queue(self):
        """
        Get job queue status

        Returns: list of jobs in the queue
        """
        tries = 0
        while tries != 10:
            try:
                cmd = ['squeue', '-u', os.environ['USER'], '-o', '%i|%j|%o|%t']
                proc = Popen(cmd, shell=False, stderr=PIPE, stdout=PIPE)
                out, err = proc.communicate()
                if err:
                    tries += 1
                    sleep(tries)
                else:
                    break
            except:
                sleep(1)
        if tries == 10:
            raise Exception('SLURM ERROR: Transport endpoint is not connected')

        queueinfo = []
        for item in out.split(b'\n')[1:]:
            if not item:
                break
            line = [x for x in item.split(b'|') if x]
            queueinfo.append({
                'JOBID': line[0],
                'NAME': line[1],
                'COMMAND': line[2],
                'STATE': line[3],
            })
        return queueinfo
    # -----------------------------------------------

    def cancel(self, job_id):
        tries = 0
        while tries != 10:
            try:
                cmd = ['scancel', str(job_id)]
                proc = Popen(cmd, shell=False, stderr=PIPE, stdout=PIPE)
                out, err = proc.communicate()
                if 'Transport endpoint is not connected' in err or err:
                    tries += 1
                    sleep(tries)
                else:
                    return True
            except Exception as e:
                print_debug(e)
                sleep(1)
        return False
    # -----------------------------------------------
