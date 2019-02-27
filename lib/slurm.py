import os
import logging
from time import sleep
from subprocess import Popen, PIPE
from .jobinfo import JobInfo


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
        out, err = self._submit('sbatch', cmd, sargs)
        if err:
            raise Exception('SLURM ERROR: ' + err)
        out = out.split()
        if 'error' in out:
            return 0
        job_id = int(out[-1])
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
            if 'Transport endpoint is not connected' in err or 'Socket timed out on send/recv operation' in err:
                qinfo = self.queue()
                for job in qinfo:
                    if job.get('COMMAND') == cmd[1]:
                        return 'Submitted batch job {}'.format(job['JOBID']), None
                print('Unable to submit job, trying again')
            elif 'Batch job submission failed' in out:
                raise Exception(out)
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
                if 'Transport endpoint is not connected' in err:
                    sleep(1)
                else:
                    success = True
            except:
                success = False
                sleep(1)

        if 'Invalid job id specified' in err:
            raise Exception('SLURM ERROR: ' + err)
        job_info = JobInfo()
        for item in out.split('\n'):
            for j in item.split(' '):
                index = j.find('=')
                if index <= 0:
                    continue
                attribute = self.slurm_to_jobinfo(j[:index])
                if attribute is None:
                    continue
                job_info.set_attr(
                    attr=attribute,
                    val=j[index + 1:])
        return job_info
    # -----------------------------------------------
    def slurm_to_jobinfo(self, attr):
        if attr == 'Partition':
            return 'PARTITION'
        elif attr == 'Command':
            return 'COMMAND'
        elif attr == 'UserId':
            return 'USER'
        elif attr == 'JobName':
            return 'NAME'
        elif attr == 'JobState':
            return 'STATE'
        elif attr == 'JobId':
            return 'JOBID'
        elif attr == 'RunTime':
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
        while 'Transport endpoint is not connected' in out and not e:
            sleep(1)
            p = Popen([cmd], stderr=PIPE, stdout=PIPE, shell=True)
            err, out = p.communicate()
        return int(out)
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
                if 'Transport endpoint is not connected' in err:
                    tries += 1
                    sleep(tries)
                else:
                    break
            except:
                sleep(1)
        if tries == 10:
            raise Exception('SLURM ERROR: Transport endpoint is not connected')

        queueinfo = []
        for item in out.split('\n')[1:]:
            if not item:
                break
            line = [x for x in item.split('|') if x]
            queueinfo.append({
                'JOBID': line[0],
                'NAME': line[1],
                'COMMAND': line[2],
                'STATE': line[3],
            })
        return queueinfo
    # -----------------------------------------------
