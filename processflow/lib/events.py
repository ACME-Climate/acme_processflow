from datetime import datetime


class Event(object):
    """
    A simple data wrapper for event information

    Parameters:
        time (datetime): The time the event took place
        message (str): The message the event should display
        data (job, optional): The job that spawned the message
    """

    def __init__(self, **kwargs):
        self._time = kwargs.get('time')
        self._message = kwargs.get('message')
        self._data = kwargs.get('data')

    @property
    def time(self):
        return self._time

    @time.setter
    def time(self, ntime):
        if not isinstance(ntime, datetime):
            raise ValueError("time must be a datetime object")
        self._time = ntime

    @property
    def message(self):
        return self._message

    @message.setter
    def message(self, nmessage):
        self._message = nmessage

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, ndata):
        self._data = ndata


class EventList(object):
    """
    A list for holding global events

    Parameters:
        event_list (list): list of events
    """

    def __init__(self):
        self._list = []

    def push(self, message, **kwargs):
        """
        Push an event into the event_list

        Args:
            message (str): The string the event will holding
            data (job: optional): The job that spawned the event
        """
        data = kwargs.get('data')
        event = Event(
            time=datetime.now(),
            message=message,
            data=data)
        self._list.append(event)

    @property
    def list(self):
        return self._list

    def replace(self, index, message):
        if index == 0 and len(self._list) == 0:
            self.push(message)
            return
        if index >= len(self._list) or index < 0:
            raise ValueError('Index {0} out of range {1}'.format(
                index, len(self._list)))
        self._list[index].message = message
