import inspect
import os
import sys
import unittest

 

from processflow.lib.mailer import Mailer
from processflow.lib.util import print_message


class TestMailer(unittest.TestCase):

    def test_send_mail_valid(self):
        print '\n'; print_message('---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        m = Mailer(
            src='baldwin32@llnl.gov',
            dst='baldwin32@llnl.gov')
        ret = m.send(
            status='THIS IS A TEST',
            msg='THIS IS ONLY A TEST')
        self.assertTrue(ret)

    def test_send_mail_invalid(self):
        print '\n'; print_message('---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        m = Mailer(
            src='xxyyzz',
            dst='xxyyzz')
        ret = m.send(
            status='THIS IS A TEST',
            msg='THIS IS ONLY A TEST')
        self.assertFalse(ret)


if __name__ == '__main__':
    unittest.main()
