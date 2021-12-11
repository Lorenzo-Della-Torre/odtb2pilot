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

"""
Add results from Hilding test to JAKOB db and the cynosure message bus
"""

import logging
from secrets import token_urlsafe
from datetime import datetime

import epsmsgbus
from hilding import get_conf

# we choose to use 7 bytes here to use the same token length as pmt
TOKEN_LENGTH = 7

log = logging.getLogger("analytics")


def lack_testcases():
    """the testsuite does not have any started testcases"""
    return bool(epsmsgbus.core.testsuite().testcases == [])

def get_analytics():
    """ Get analytics config """
    return get_conf().rig.analytics

def require_use_epsmsgbus(func):
    """ Decorator to disable func if analytics is not configured """
    def wrapper_require_use_epsmsgbus(*args, **kwargs):
        if get_analytics().analytics:
            func(*args, **kwargs)
    return wrapper_require_use_epsmsgbus

class TestSuiteDataAdapter(epsmsgbus.TestSuiteDataAdapter):
    """Hilding Test Suite"""
    def __init__(
            self,
            name=get_analytics().test_suite_name,
            identifier=get_analytics().test_suite_identifier,
            jobid="SET_JOBID"):
        self.name = name
        self.id = identifier # pylint: disable=invalid-name
        self.jobid = jobid

    # OPTIONAL fields ----------------------------------------------------{{{3
    def get_product_name(self):
        """Return product ID. This is Cynosure specific and should be similar
        to the activity id (or maybe even the same)."""
        return self.name

    def get_product_id(self):
        """Return product ID. This is Cynosure specific and should be similar
        to the activity id (or maybe even the same)."""
        return self.id

    def get_execution_info(self):
        """Return information about the test execution itself."""
        return epsmsgbus.ExecutionInfo(
                name=self.jobid,
                description=get_analytics().test_suite_description,
                executor=get_analytics().executor)

    def get_simulation_info(self): #pylint: disable=no-self-use
        """Return information about the virtual simulation model running on
        Hilding"""
        project = get_analytics().project
        ecu = get_analytics().ecu
        token = token_urlsafe(nbytes=TOKEN_LENGTH)
        date =  datetime.utcnow().date()
        build_id = f"HD_BUILD_{project}_{ecu}_{date}_{token}"
        return epsmsgbus.SimulationInfo(
                build_id=build_id,
                project=project,
                branch=get_analytics().branch,
                ecu=ecu,
                dbc=get_analytics().dbc)


    def get_software_info(self): #pylint: disable=no-self-use
        """Return information about the software under test."""
        return epsmsgbus.SoftwareInfo(
                ecu=get_analytics().ecu,
                platform=get_analytics().platform,
                vehicle_project=get_analytics().vehicle_project,
                vehicle_series=get_analytics().vehicle_series,
                version=get_analytics().sw_version,
                # this should be the githash for the firmware
                githash=get_analytics().sw_githash,
                changeset=get_analytics().sw_changeset,
                inhousechangeset=get_analytics().sw_inhousechangeset)

    def get_testenv_info(self): #pylint: disable=no-self-use
        """Return information about the test environment."""
        return epsmsgbus.TestEnvironmentinfo(
                name=get_analytics().testenv_info_name,
                description=get_analytics().testenv_info_description,
                platform=get_analytics().platform)


class TestCaseDataAdapter(epsmsgbus.TestCaseDataAdapter): #pylint: disable=too-few-public-methods
    """Adapter for metadata from test cases and test steps. Only 'get_taskid()'
    is mandatory."""
    def __init__(self, name):
        self.name = name


class TestStepDataAdapter(epsmsgbus.TestStepDataAdapter): #pylint: disable=too-few-public-methods
    """Hilding adapter for test steps"""
    def get_testcode_info(self): #pylint: disable=no-self-use
        """Get testcode info"""
        # No requirement info on test step level
        return epsmsgbus.TestCodeInfo(
                author='Hilding',
                description='Hilding test step',
                creationdate=datetime(2021, 3, 1, 0, 10),
                modificationdate=datetime.utcnow())


# Just for convenience
@require_use_epsmsgbus
def testsuite_started():
    """Signal that test suite started. Link adapter and API function."""
    date =  datetime.utcnow().date()
    token = token_urlsafe(nbytes=TOKEN_LENGTH)
    jobid = f"HD_JOB_{date}_{token}"
    adapter = TestSuiteDataAdapter(jobid=jobid)
    epsmsgbus.testsuite_started(adapter, adapter.name)
    log.debug("testsuite_started: jobid=%s", jobid)


@require_use_epsmsgbus
def testsuite_ended():
    """Signal that test suite ended. Link adapter and API function."""
    # No verdict = use the worst verdict of the test cases
    epsmsgbus.testsuite_ended()

    # this should probably be done in epsmsgbus, but let's put it here for now
    epsmsgbus.core.testsuite().testcases = []
    log.debug("testsuite_ended")


@require_use_epsmsgbus
def testcase_started(name):
    """Signal that test case ended. Link adapter and API function."""
    adapter = TestCaseDataAdapter(name)
    epsmsgbus.testcase_started(adapter, name)
    log.debug("testcase_started: %s", name)


@require_use_epsmsgbus
def testcase_ended(verdict):
    """Signal that test case ended. Link adapter and API function."""
    epsmsgbus.testcase_ended(verdict)
    log.debug("testcase_ended: verdict=%s", verdict)


@require_use_epsmsgbus
def teststep_started(name):
    """Signal that test step started. Link adapter and API function."""
    adapter = TestStepDataAdapter()
    epsmsgbus.teststep_started(adapter, name)
    log.debug("teststep_started: %s", name)


@require_use_epsmsgbus
def teststep_ended(verdict):
    """Signal that test step ended. Link adapter and API function."""
    epsmsgbus.teststep_ended(verdict)
    log.debug("teststep_ended: verdict=%s", verdict)

@require_use_epsmsgbus
def messagehandler(use_db=False, use_mq=False):
    """Configure what to connect to"""
    epsmsgbus.messagehandler(use_db, use_mq)
    log.debug("messagehandler: use_db=%s use_mq=%s", use_db, use_mq)
