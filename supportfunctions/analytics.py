"""
Add results from ODTB2 test to JAKOB db and the cynosure message bus
"""

import sys
from secrets import token_urlsafe
from datetime import datetime

import epsmsgbus

import odtb_conf

required_attr = [
    "TEST_SUITE_NAME",
    "TEST_SUITE_IDENTIFIER",
    "TEST_SUITE_DESCRIPTION",
    "EXECUTOR",
    "PROJECT",
    "PLATFORM",
    "BRANCH",
    "ECU",
    "DBC",
    "VEHICLE_PROJECT",
    "VEHICLE_SERIES",
    "SW_VERSION",
    "SW_GITHASH",
    "SW_CHANGESET",
    "SW_INHOUSECHANGESET",
    "TESTENV_INFO_NAME",
    "TESTENV_INFO_DESCRIPTION",
    "TESTENV_INFO_PLATFORM",
]

def analytics_config(name):
    """Get config names or a default dummy value"""
    return getattr(odtb_conf, name, "UNKNOWN")

def require_use_epsmsgbus(func):
    """Decorator to disable func if odtb_conf.USE_EPSMSGBUS is not True"""
    def wrapper_require_use_epsmsgbus(*args, **kwargs):
        if getattr(odtb_conf, "USE_EPSMSGBUS", False):
            for attr in required_attr:
                if not hasattr(odtb_conf, attr):
                    sys.exit(f"analytics error: {attr} is not configured in odtb_conf")
            func(*args, **kwargs)
    return wrapper_require_use_epsmsgbus

class Odtb2TestSuiteDataAdapter(epsmsgbus.TestSuiteDataAdapter):
    """ODTB2 Test Suite"""
    def __init__(
            self,
            name=analytics_config("TEST_SUITE_NAME"),
            identifier=analytics_config("TEST_SUITE_IDENTIFIER"),
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
                description=analytics_config("TEST_SUITE_DESCRIPTION"),
                executor=analytics_config("EXECUTOR"))

    def get_simulation_info(self):
        """Return information about the virtual simulation model running on the
        HIL simulator."""
        project = analytics_config("PROJECT")
        ecu = analytics_config("ECU")
        token = token_urlsafe(7)
        date =  datetime.utcnow().date()
        build_id = f"ODTB2_{project}_{ecu}_{date}_{token}"
        return epsmsgbus.SimulationInfo(
                build_id=build_id,
                project=project,
                branch=analytics_config("BRANCH"),
                ecu=ecu,
                dbc=analytics_config("DBC"))


    def get_software_info(self):
        """Return information about the software under test."""
        return epsmsgbus.SoftwareInfo(
                ecu=analytics_config("ECU"),
                platform=analytics_config("PLATFORM"),
                vehicle_project=analytics_config("VEHICLE_PROJECT"),
                vehicle_series=analytics_config("VEHICLE_SERIES"),
                version=analytics_config("SW_VERSION"),
                githash=analytics_config("SW_GITHASH"),
                changeset=analytics_config("SW_CHANGESET"),
                inhousechangeset=analytics_config("SW_INHOUSECHANGESET"))

    def get_testenv_info(self):
        """Return information about the test environment."""
        return epsmsgbus.TestEnvironmentinfo(
                name=analytics_config("TESTENV_INFO_NAME"),
                description=analytics_config("TESTENV_INFO_DESCRIPTION"),
                platform=analytics_config("TESTENV_INFO_PLATFORM"))


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
