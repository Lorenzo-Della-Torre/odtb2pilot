/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



**********************************************************************************/


#!/bin/env python
"""
Core data structures for passing messages from test cases to a message bus
and/or a database.

Currently it works a the messages are created and posted on Cynosure.
The same message is saved to the database by the client.

In the future we may want to only publish messages on the bus and let a
database service handle the persistence layer of the database.
That would relieve the process that handles test results from having to be
connected to a database.
"""

import datetime
import uuid


# Enumerations ==========================================================={{{1
class EnumerationValue(object):
    """Base class for enumerations (of states).  The name is a string and the
    value is a number."""

    values = {}

    def __init__(self, value):
        """The argument 'value' can either be the string representation or the
        numeric value."""
        if isinstance(value, (int, float)):
            self.value = value if value in self.values else 0
        else:
            names = {v: k for k, v in self.values.items()}
            self.value = names.get(value.lower(), 0)

    @property
    def name(self):
        return self.values.get(self.value, 'unknown')

    def __eq__(self, other):
        return self.value == other.value

    def __ne__(self, other):
        return self.value != other.value

    def __gt__(self, other):
        return self.value > other.value

    def __ge__(self, other):
        return self.value >= other.value

    def __lt__(self, other):
        return self.value < other.value

    def __le__(self, other):
        return self.value <= other.value

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<{} {} ({})>'.format(self.__class__.__name__, self.name, self.value)


class Status(EnumerationValue):
    """Enumeration of states (in Cynosure). The state 'unknown' is self
    explanatory.  'queued' and 'allocated' are not used by us. 'disabled' is
    set for jobs that did not run for any reason, including jobs that had
    errors that prevented them from finishing."""
    values = {
        0: "unknown",
        1: "queued",
        2: "allocated",
        3: "ongoing",
        4: "finished",
        5: "disabled",
    }


class Verdict(EnumerationValue):
    """
    Verdicts have values In order of severity, that means that
    the aggregated verdict from a chain of events is the verdict
    with the highest numeric value.

    --------------  --------  ---------------------------------------
    AutomationDesk  Cynosure  Comment
    --------------  --------  ---------------------------------------
    Executed        unknown
    Passed          passed
    Undefined       unknown
    Failed          failed
    Error           errored
    N/A             skipped
    N/A             aborted   Use for test cases that never finished
    --------------  --------  ---------------------------------------
    """
    values = {
        0: 'unknown',
        1: 'passed',
        3: 'skipped',
        4: 'failed',
        5: 'errored',
        6: 'skipped',
        7: 'aborted',
    }


# Observer / Observable pattern =========================================={{{1
class Observable(object):
    """Base class for an object that can dynamically register one or more
    observers.  When an event happens, then each of the observers is called."""
    def __init__(self):
        self.observers = []

    def register(self, observer):
        self.observers.append(observer)

    def unregister(self, observer):
        # Maybe we should protect this, ValueError may be raised.
        self.observers.remove(observer)

    def notify_abort(self):
        for observer in self.observers:
            observer.notify_abort(self)

    def notify_start(self):
        for observer in self.observers:
            observer.notify_start(self)

    def notify_finish(self, verdict):
        for observer in self.observers:
            observer.notify_finish(self, verdict)


class Observer(object):
    """Base class for observers. Each observer needs to implement the methods."""

    def notify_abort(self, observable):
        raise NotImplementedError("Method 'notify_abort' not implemented. Define ia a subclass.")

    def notify_start(self, observable):
        raise NotImplementedError("Method 'notify_start' not implemented. Define ia a subclass.")

    def notify_finish(self, observable, verdict):
        raise NotImplementedError("Method 'notify_finish' not implemented. Define ia a subclass.")


class Container(dict):
    """Generic container object for holding metadata."""
    pass


class TestSuite(Observable):
    """Base class for test suites. Holds a number of "first-level" attributes.
    All other metdata is saved in a Container() object."""

    def __init__(self, name, identifier=None):
        super(TestSuite, self).__init__()
        self.name = name
        self.id = str(uuid.uuid4()) if identifier is None else identifier
        self.verdict = Verdict('unknown')
        self.state = Status('unknown')
        self.starttime = self.endtime = None
        self.current_testcase = None
        self.url = None
        self.logs = []
        self.testcases = []
        self.metadata = Container()

    def abort_unfinished(self):
        for testcase in self.testcases:
            if testcase.state.name != 'finished':
                testcase.abort()

    def abort(self):
        """Execution is aborted. Make sure that all unfinished test cases and
        test steps are "closed". Notify observers."""
        self.abort_unfinished()
        self.endtime = datetime.datetime.utcnow()
        self.state = Status('disabled')
        self.verdict = Verdict('aborted')
        self.notify_abort()

    def start(self):
        """Set start time and set state to 'ongoing'. Notify observers."""
        self.starttime = datetime.datetime.utcnow()
        self.state = Status('ongoing')
        self.notify_start()

    def finish(self, verdict=None):
        """Set end time and set state to 'finished'. Save verdict and notify
        observers.

        NOTE: If verdict is None, the verdict is calculated from the test cases
              in the test suite.
        """
        self.abort_unfinished()
        self.endtime = datetime.datetime.utcnow()
        self.state = Status('finished')
        if verdict is not None:
            self.verdict = Verdict(verdict)
        self.notify_finish(self.verdict)

    def update_verdict(self, verdict):
        """Update my verdict, this is called from a test case object."""
        self.verdict = max(self.verdict, Verdict(verdict))

    def testcase(self, name=None, identifier=None):
        """Return corrent test case or create a new data structure for a test
        case."""
        if name is not None:
            self.current_testcase = TestCase(parent=self, name=name, identifier=identifier)
            self.testcases.append(self.current_testcase)
        return self.current_testcase


class TestCase(Observable):
    """Base class for test cases."""
    def __init__(self, parent, name, identifier=None):
        super(TestCase, self).__init__()
        self.parent = parent
        self.name = name
        self.id = str(uuid.uuid4()) if identifier is None else identifier
        self.verdict = Verdict('unknown')
        self.state = Status('unknown')
        self.starttime = self.endtime = None
        self.url = None
        self.logs = []
        self.current_teststep = None
        self.teststeps = []
        self.metadata = Container()

    def abort_unfinished(self):
        """Run abort() for all test steps that are not finished within the test
        case."""
        for teststep in self.teststeps:
            if teststep.state.name != 'finished':
                teststep.abort()

    def abort(self):
        """Abort unfihisned test steps and set state/verdict to
        'disabled/aborted'. Notify observers."""
        self.abort_unfinished()
        self.endtime = datetime.datetime.utcnow()
        self.state = Status('disabled')
        self.verdict = Verdict('aborted')
        # pass verdict to parent (test suite)
        self.parent.update_verdict('aborted')
        self.notify_abort()

    def start(self):
        """Start the test case and set start tiee and state. Notify observers"""
        self.starttime = datetime.datetime.utcnow()
        self.state = Status('ongoing')
        self.notify_start()

    def finish(self, verdict):
        """Finish the test case and set start tiee and state. Notify observers.
        Any unfinished test steps will be set as 'aborted'."""
        # Let the test suite object get the verdict.
        self.parent.update_verdict(verdict)
        self.abort_unfinished()
        self.endtime = datetime.datetime.utcnow()
        self.state = Status('finished')
        self.verdict = Verdict(verdict)
        self.notify_finish(self.verdict)

    def teststep(self, name=None, identifier=None):
        """Return current test step or create a new test step."""
        if name is not None:
            self.current_teststep = TestStep(parent=self, name=name, identifier=identifier)
            self.teststeps.append(self.current_teststep)
        return self.current_teststep


class TestStep(Observable):
    """Base class for test steps."""
    def __init__(self, parent, name, identifier=None):
        super(TestStep, self).__init__()
        self.parent = parent
        self.name = name
        self.id = str(uuid.uuid4()) if identifier is None else identifier
        self.verdict = Verdict('unknown')
        self.state = Status('unknown')
        self.starttime = self.endtime = None
        self.url = None
        self.logs = []
        self.metadata = Container()

    def abort(self):
        """Abort and notify observers."""
        self.endtime = datetime.datetime.utcnow()
        self.state = Status('disabled')
        self.verdict = Verdict('aborted')
        self.notify_abort()

    def start(self):
        """Start and notify observers."""
        self.starttime = datetime.datetime.utcnow()
        self.state = Status('ongoing')
        self.notify_start()

    def finish(self, verdict):
        """Finish and notify observers."""
        self.endtime = datetime.datetime.utcnow()
        self.state = Status('finished')
        self.verdict = Verdict(verdict)
        self.notify_finish(self.verdict)


try:
    CURRENT_TESTSUITE
except NameError:
    # Should not happen, but just in case...
    CURRENT_TESTSUITE = TestSuite('unknown')


def testsuite(name=None, identifier=None):
    """Factory function that returns current test suite or creates a new test
    suite object depending on if the 'name' argument was given."""
    global CURRENT_TESTSUITE
    if name is not None:
        CURRENT_TESTSUITE = TestSuite(name, identifier)
    return CURRENT_TESTSUITE


# eof
