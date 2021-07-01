#!/bin/env python
"""
API For:

  * Sending data messages to Cynosure message bus

 and/or

  * Saving data in "Jakob" database


Use like this:
    # Import API
    import epsmsgbus.api

    # Define your adapters


"""
import epsmsgbus.core as core
import epsmsgbus.data as data
import epsmsgbus.cynosure2 as cynosure2

# To be used by client code
from epsmsgbus.core import Verdict
from epsmsgbus.data import ExecutionInfo
from epsmsgbus.data import SimulationInfo
from epsmsgbus.data import SoftwareInfo
from epsmsgbus.data import TestCodeInfo
from epsmsgbus.data import TestEnvironmentinfo
from epsmsgbus.data import TestSuiteDataAdapter
from epsmsgbus.data import TestCaseDataAdapter
from epsmsgbus.data import TestStepDataAdapter
from epsmsgbus.cynosure2 import messagehandler


__all__ = ['messagehandler', 'Verdict', 'ExecutionInfo', 'TestEnvironmentinfo',
        'SimulationInfo', 'TestCodeInfo', 'SoftwareInfo',
        'TestSuiteDataAdapter', 'TestCaseDataAdapter', 'TestStepDataAdapter',
        'testsuite_started', 'testsuite_ended',
        'testcase_started', 'testcase_ended',
        'teststep_started', 'teststep_ended']


def testsuite_started(adapter, name, identifier=None):
    """Call when a test suite is started.

    'name' is the name of the test suite (as it will be used in reports).
    'adapter' is an adapter for retrieving metadata.
    """
    ts = core.testsuite(name=name, identifier=identifier)
    ts.register(data.TestSuiteDataObserver(adapter))
    ts.register(cynosure2.TestSuiteMessageObserver(messagehandler()))
    ts.start()


def testsuite_ended(verdict=None):
    """Call when a test suite is finished.

    'verdict' is one of:
      ('unknown', 'passed', 'skipped', 'failed', 'errored', 'skipped', 'aborted')
    """
    assert verdict in Verdict.values.values() or verdict is None, 'Invalid verdict, must be one of: %s' % Verdict.values.values()
    ts = core.testsuite()
    ts.finish(verdict)


def testcase_started(adapter, name, identifier=None):
    """Call when a test case is started.

    'name' is the name of the test case (as it will be used in reports).
    'adapter' is an adapter for retrieving metadata.
    """
    tc = core.testsuite().testcase(name=name, identifier=identifier)
    tc.register(data.TestCaseDataObserver(adapter))
    tc.register(cynosure2.TestCaseMessageObserver(messagehandler()))
    tc.start()


def testcase_ended(verdict):
    """Call when a test case is finished.

    'verdict' is one of:
      ('unknown', 'passed', 'skipped', 'failed', 'errored', 'skipped', 'aborted')
    """
    assert verdict in Verdict.values.values(), 'Invalid verdict, must be one of: %s' % Verdict.values.values()
    tc = core.testsuite().testcase()
    tc.finish(verdict)


def teststep_started(adapter, name, identifier=None):
    """Call when a test step is started.

    'name' is the name of the test step (as it will be used in reports).
    'adapter' is an adapter for retrieving metadata.
    """
    ts = core.testsuite().testcase().teststep(name=name, identifier=identifier)
    ts.register(data.TestStepDataObserver(adapter))
    ts.register(cynosure2.TestStepMessageObserver(messagehandler()))
    ts.start()


def teststep_ended(verdict):
    """Call when a test step is finished.

    'verdict' is one of:
      ('unknown', 'passed', 'skipped', 'failed', 'errored', 'skipped', 'aborted')
    """
    assert verdict in Verdict.values.values(), 'Invalid verdict, must be one of: %s' % Verdict.values.values()
    core.testsuite().testcase().teststep().finish(verdict)


# eof