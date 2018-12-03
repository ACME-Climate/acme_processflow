import unittest
import os, sys
import inspect

if sys.path[0] != '.':
    sys.path.insert(0, os.path.abspath('.'))


from lib.slurm import Slurm
from lib.util import print_message

class TestSlurm(unittest.TestCase):

    def test_batch(self):
        print('\n'); print_message('---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        slurm = Slurm()
        command = os.path.join('tests', 'test_slurm_batch.sh')
        job_id = slurm.batch(command, '-n 1 -N 1')
        self.assertTrue(job_id)
        self.assertTrue(isinstance(job_id, int))

        info = slurm.showjob(job_id)
        allowed_states = ['PENDING', 'RUNNING', 'COMPLETE', 'COMPLETING']
        self.assertTrue(info['JobState'] in allowed_states)

        info = slurm.queue()
        in_queue = False
        for item in info:
            if int(item['JOBID']) == job_id:
                in_queue = True
                self.assertTrue(item['STATE'] in ['PD', 'R'])
                break
        self.assertTrue(in_queue)
        slurm.cancel(job_id)

    def test_shownode(self):
        print('\n'); print_message('---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        slurm = Slurm()
        node = os.environ['HOSTNAME'].lower().split('.')[0]
        node_info = slurm.shownode(node)
        self.assertTrue(node_info['Arch'] == 'x86_64')


if __name__ == '__main__':
    unittest.main()
