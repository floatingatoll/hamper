import os
import re
import stat
import sys
import pprint
from twisted.internet import reactor

pp = pprint.PrettyPrinter(indent=4)

class NagiosAlert(object):
    """Classifies an Alert and raises it into a pythonic object."""
    def __init__(self, raw_line):
        self.raw_line = raw_line
        self.is_valid , self.is_ackable = True, False
        def classify_line(alert, raw_line):
            m = re.match(
                "^\[(?P<timestamp>\d+)\]\s"
                "(?P<alert_type>[\w\s]*):\s"
                "(?P<group>\w*);"
                "(?P<raw_data>.*)",
                raw_line)
            if m:
                for attr, value in m.groupdict().iteritems():
                    setattr(alert, attr, value)
                alert.is_ackable = True  # True until proven otherwise
                return

            alert.is_valid = False

        classify_line(self, raw_line)
        if not self.is_valid:
            return
        if self.alert_type == 'SERVICE NOTIFICATION':
            hostnamej


    def __str__(self):
        return "{timestamp} {alert_type} {group}".format(**vars(self))

    def __repr__(self):
        return "<NagiosAlert: {0}".format(self)

class AlertBuffer(object):
    def __init__(self, SIZE=5):
        self.size = SIZE
        self.pos = 0
        self.alert_buffer = [None] * SIZE  # The actual list object we manipulate

    def add(self, item):
        print self.pos
        self.alert_buffer[self.pos] = item
        self.pos += 1
        self.pos %= self.size
        pp.pprint(self.alert_buffer)
        print ""

class LogQueue(object):
    """Handle the never ending queue of lines from Nagios' log file. Add them
    to a a list."""

    def __init__(self, filename, whence=os.SEEK_END):
        self.filename = filename
        self.fd = open(filename)
        self.fd.seek(0, whence)
        self.fstat = os.fstat(self.fd.fileno())
        self.check_freq = 1
        self.queue = []

    def next(self):
        if not self.queue:
            return None
        return self.queue.pop(0)

    def process_read(self, data):
        for line in data.split('\n'):
            if not line:
                continue

            alert = NagiosAlert(line)
            if alert.is_valid:
                self.queue.append(alert)

    def fd_identity(self, struct_stat):
        return struct_stat[stat.ST_DEV], struct_stat[stat.ST_INO]

    def fd_rotate(self):
        self.fd = open(self.filename)  # From the beginning!
        self.fstat = os.fstat(self.fd.fileno())

    def tailfile(self):
        self.process_read(self.fd.read())
        cur_stat = os.fstat(self.fd.fileno())
        if self.fd_identity(cur_stat) != self.fd_identity(self.fstat):
            self.fd_rotate()
        reactor.callLater(self.check_freq, lambda: self.tailfile())

    def __str__(self):
        pp.pprint(self.queue)
    def __repr__(self):
        pp.pprint(self.queue)


class NagiosAlertProcessor(object):
    """A circular linked list that contains Alerts. The list has a static size."""
    def __init__(self, filename, SIZE=10, FREQ=1):
        self.filename = filename
        self.freq = FREQ
        self.queue = LogQueue(self.filename, whence=os.SEEK_CUR)
        self.queue.tailfile()
        self.alert_buffer = AlertBuffer()

    def start(self):
        alert = self.queue.next()
        if alert:
            alert.alert_idx = self.alert_buffer.pos
            self.alert_buffer.add(alert)
            self.process(alert)
        reactor.callLater(self.freq, lambda: self.start())

    def process(self, alert):
        """Send message to irc and stuff"""
        print "Processing alert: "+str(alert)

if __name__ == '__main__':
    processor = NagiosAlertProcessor(sys.argv[1])
    processor.start()
    reactor.run()
