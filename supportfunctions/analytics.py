"""
Add results from ODTB2 test to JAKOB db and the cynosure message bus
"""

from secrets import token_urlsafe
from datetime import datetime

import epsmsgbus

import odtb_conf

def require_use_epsmsgbus(func):
    """Decorator to disable func if odtb_conf.USE_EPSMSGBUS is not True"""
    def wrapper_require_use_epsmsgbus(*args, **kwargs):
        if getattr(odtb_conf, "USE_EPSMSGBUS", False):
            func(*args, **kwargs)
    return wrapper_require_use_epsmsgbus

class Odtb2TestSuiteDataAdapter(epsmsgbus.TestSuiteDataAdapter):
    """ODTB2 Test Suite"""
    def __init__(
            self,
            name=odtb_conf.TEST_SUITE_NAME,
            identifier=odtb_conf.TEST_SUITE_IDENTIFIER,
            jobid='SET_JOBID'):
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
                description=odtb_conf.TEST_SUITE_DESCRIPTION,
                executor=odtb_conf.EXECUTOR)

    def get_simulation_info(self):
        """Return information about the virtual simulation model running on the
        HIL simulator."""
        project = odtb_conf.PROJECT
        ecu = odtb_conf.ECU
        token = token_urlsafe(7)
        date =  datetime.utcnow().date()
        build_id = f"ODTB2_{project}_{ecu}_{date}_{token}"
        return epsmsgbus.SimulationInfo(
                build_id=build_id,
                project=project,
                branch=odtb_conf.BRANCH,
                ecu=ecu,
                dbc=odtb_conf.DBC)


    def get_software_info(self):
        """Return information about the software under test."""
        return epsmsgbus.SoftwareInfo(
                ecu=odtb_conf.ECU,
                platform=odtb_conf.PLATFORM,
                vehicle_project=odtb_conf.VEHICLE_PROJECT,
                vehicle_series=odtb_conf.VEHICLE_SERIES,
                version=odtb_conf.SW_VERSION,
                githash=odtb_conf.SW_GITHASH,
                changeset=odtb_conf.SW_CHANGESET,
                inhousechangeset=odtb_conf.SW_INHOUSECHANGESET)

    def get_testenv_info(self):
        """Return information about the test environment."""
        return epsmsgbus.TestEnvironmentinfo(
                name=odtb_conf.TESTENV_INFO_NAME,
                description=odtb_conf.TESTENV_INFO_DESCRIPTION,
                platform=odtb_conf.TESTENV_INFO_PLATFORM)


class Odtb2TestCaseDataAdapter(epsmsgbus.TestCaseDataAdapter):
    """Adapter for metadata from test cases and test steps. Only 'get_taskid()'
    is mandatory."""
    def __init__(self, name):
        self.name = name


class Odtb2TestStepDataAdapter(epsmsgbus.TestStepDataAdapter):
    """ODTB2 adapter for test steps"""
    def get_testcode_info(self):
        # No requirement info on test step level
        return epsmsgbus.TestCodeInfo(
                author='ODTB2',
                description='ODTB2 test step',
                creationdate=datetime(2021, 3, 1, 0, 10),
                modificationdate=datetime.utcnow())


# Just for convenience
@require_use_epsmsgbus
def testsuite_started():
    """Signal that test suite started. Link adapter and API function."""
    date =  datetime.utcnow().date()
    token = token_urlsafe(7)
    jobid = f"ODTB2_JOB_{date}_{token}"
    adapter = Odtb2TestSuiteDataAdapter(jobid=jobid)
    epsmsgbus.testsuite_started(adapter, adapter.name)


@require_use_epsmsgbus
def testsuite_ended():
    """Signal that test suite ended. Link adapter and API function."""
    # No verdict = use the worst verdict of the test cases
    epsmsgbus.testsuite_ended()


@require_use_epsmsgbus
def testcase_started(name):
    """Signal that test case ended. Link adapter and API function."""
    adapter = Odtb2TestCaseDataAdapter(name)
    epsmsgbus.testcase_started(adapter, name)


@require_use_epsmsgbus
def testcase_ended(verdict, combine_steps=False):
    """Signal that test case ended. Link adapter and API function."""
    if combine_steps:
        teststep_ended(verdict)
    epsmsgbus.testcase_ended(verdict)


@require_use_epsmsgbus
def teststep_started(name):
    """Signal that test step started. Link adapter and API function."""
    adapter = Odtb2TestStepDataAdapter()
    epsmsgbus.teststep_started(adapter, name)


@require_use_epsmsgbus
def teststep_ended(verdict):
    """Signal that test step ended. Link adapter and API function."""
    epsmsgbus.teststep_ended(verdict)

@require_use_epsmsgbus
def messagehandler(use_db=False, use_mq=False):
    """Configure what to connect to"""
    epsmsgbus.messagehandler(use_db, use_mq)
