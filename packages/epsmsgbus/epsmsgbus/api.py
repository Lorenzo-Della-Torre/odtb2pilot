"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

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
import importlib

import epsmsgbus.core as core
import epsmsgbus.data as data

import epsconfig
# To be used by client code
from epsmsgbus.core import Verdict
from epsmsgbus.data import ExecutionInfo
from epsmsgbus.data import SimulationInfo
from epsmsgbus.data import SoftwareInfo
from epsmsgbus.data import TestCodeInfo
from epsmsgbus.data import VerdictInfo
from epsmsgbus.data import TestEnvironmentinfo
from epsmsgbus.data import TestSuiteDataAdapter
from epsmsgbus.data import TestCaseDataAdapter
from epsmsgbus.data import TestStepDataAdapter
import epsmsgbus.activityid as activity_mod

from epsmsgbus.cynosure import messagehandler


config = epsconfig.config('db')
if config.cynosure.major_version is None:
    raise ValueError("Cynosure major version is not configured!")
cynosure_msg = importlib.import_module('epsmsgbus.cynosure{}'.format(config.cynosure.major_version))


__all__ = ['messagehandler', 'Verdict', 'ExecutionInfo', 'TestEnvironmentinfo',
           'SimulationInfo', 'TestCodeInfo', 'SoftwareInfo', 'VerdictInfo',
        'TestSuiteDataAdapter', 'TestCaseDataAdapter', 'TestStepDataAdapter',
        'testsuite_started', 'testsuite_ended',
        'testcase_started', 'testcase_ended',
        'teststep_started', 'teststep_ended']


def testsuite_started(adapter, name, identifier=None, use_db=None):
    """Call when a test suite is started.

    'name' is the name of the test suite (as it will be used in reports).
    'adapter' is an adapter for retrieving metadata.
    """
    if activity_mod.get_activityid():
      id = activity_mod.get_activityid()
      name = id['namespace']
      id = id['instance']
      ts = core.testsuite(name=name, identifier=id)
    else:
      ts = core.testsuite(name=name, identifier=identifier)
    ts.register(data.TestSuiteDataObserver(adapter))
    ts.register(cynosure_msg.TestSuiteMessageObserver(messagehandler(use_db=use_db)))
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
    tc.register(cynosure_msg.TestCaseMessageObserver(messagehandler()))
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
    ts.register(cynosure_msg.TestStepMessageObserver(messagehandler()))
    ts.start()


def teststep_ended(verdict):
    """Call when a test step is finished.

    'verdict' is one of:
      ('unknown', 'passed', 'skipped', 'failed', 'errored', 'skipped', 'aborted')
    """
    assert verdict in Verdict.values.values(), 'Invalid verdict, must be one of: %s' % Verdict.values.values()
    core.testsuite().testcase().teststep().finish(verdict)


# eof
