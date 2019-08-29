import inspect
import os
import sys
import unittest

from datetime import datetime

 

from processflow.lib.events import EventList, Event
from processflow.lib.util import print_message


class TestEventList(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestEventList, self).__init__(*args, **kwargs)
    
    def test_event(self):
        print '\n'; print_message('---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        event = Event()

        now = datetime.now()
        event.time = now
        self.assertEquals(event.time, now)

        msg = 'This is only a test'
        event.message = msg
        self.assertEquals(event.message, msg)

        test_data = {
            'this is': 'some test data',
            'blorp': 4
        }
        event.data = test_data
        self.assertEquals(event.data, test_data)
    
    def test_event_list(self):
        print '\n'; print_message('---- Starting Test: {} ----'.format(inspect.stack()[0][3]), 'ok')
        elist = EventList()
        elist.push('beep boop', data=42)

        self.assertEquals(len(elist.list), 1)

        rmessage = 'boop beed'
        elist.replace(
            index=0,
            message=rmessage)
        self.assertEquals(elist.list[0].message, rmessage)


if __name__ == '__main__':
    unittest.main()
