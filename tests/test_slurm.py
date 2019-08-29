import inspect
import os
import sys
import unittest

 

from processflow.lib.util import print_message
from processflow.lib.slurm import Slurm


class TestSlurm(unittest.TestCase):

    def test_batch_and_cancel(self):
        print '\n'
        print_message(
            '---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        slurm = Slurm()
        command = 'tests/test_resources/test_slurm_batch.sh'
        job_id = slurm.batch(command)
        self.assertTrue(job_id)
        self.assertTrue(isinstance(job_id, int))
        self.assertNotEqual(job_id, 0)

        job_info = slurm.showjob(job_id)
        allowed_states = ['PENDING', 'RUNNING', 'COMPLETE', 'COMPLETING']
        self.assertTrue(job_info.state in allowed_states)

        info = slurm.queue()
        in_queue = False
        for item in info:
            if int(item['JOBID']) == job_id:
                in_queue = True
                break
        self.assertTrue(in_queue)
        self.assertTrue(slurm.cancel(job_id))


if __name__ == '__main__':
    unittest.main()
