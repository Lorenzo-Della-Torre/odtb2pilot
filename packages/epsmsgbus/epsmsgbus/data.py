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
Definitions of metadata and adapters and obsevers for moving data between
different objects.
"""

import uuid
from epsmsgbus.core import Observer


# Data structures for metadata  =========================================={{{1
class ExecutionInfo(object):
    """Information about the test execution itself."""
    def __init__(self, name=None, description=None, executor=None, project=None):
        self.name = name
        self.description = description
        self.executor = executor
        self.project = project


class SimulationInfo(object):
    """Information about the real time simulation application in the HIL
    simulator."""
    def __init__(self, build_id=None, project=None, branch=None,
            ecu=None, dbc=None):
        self.build_id = build_id
        self.project = project
        self.branch = branch
        self.ecu = ecu
        self.dbc = dbc


class SoftwareInfo(object):
    """Metadata about the software under test (not the test framework)."""
    def __init__(self, ecu=None, platform=None, vehicle_project=None,
            vehicle_series=None, version=None, githash=None, changeset=None,
            inhousechangeset=None):
        self.ecu = ecu
        self.platform = platform
        self.vehicle_project = vehicle_project
        self.vehicle_series = vehicle_series
        self.version = version
        self.githash = githash
        self.changeset = changeset
        self.inhousechangeset = inhousechangeset


class TestCodeInfo(object):
    """Metadata about the test case implementation (the test code)."""
    def __init__(self, author=None, description=None,
            creationdate=None, modificationdate=None,
            requirement=None, responsible=None):
        self.author = author
        self.description = description
        self.creationdate = creationdate
        self.modificationdate = modificationdate
        self.requirement = requirement
        self.responsible = responsible


class TestEnvironmentinfo(object):
    """Information about the test environment (simulator, test object, etc.)
    This data container will likely have more attributes later on."""
    def __init__(self, name=None, description=None, platform=None, ipaddress=None):
        self.name = name
        self.description = description
        self.ipaddress=ipaddress
        self.platform = platform


# Adapters for getting metadata from the test environmenbt ==============={{{1
class TestSuiteDataAdapter(object):
    """This is an adapter, not all methods need to be subclassed."""

    def get_product_name(self):
        """Return "product" name (Product). This is Cynosure specific and could
        be the based on the test suite name (or maybe even the same).

        IF this method does not return anything, the test suite name will
        be used."""
        pass

    def get_product_id(self):
        """Return "product" identifier (unique).

        If this ID is not returned, the test suite identifier will be used
        instead."""
        pass

    def get_execution_info(self):
        """Return information about the test execution itself."""
        return ExecutionInfo()

    def get_simulation_info(self):
        """Return information about the virtual simulation model running on the
        HIL simulator."""
        return SimulationInfo()

    def get_software_info(self):
        """Return information about the software under test."""
        return SoftwareInfo()

    def get_testenv_info(self):
        """Return information about the test environment."""
        return TestEnvironmentinfo()

    def get_logs(self):
        """Return list of URL's to optional log files or recorded data."""
        return []

    def get_url(self):
        """Return URL to the test report."""
        pass


class TestCaseDataAdapter(object):
    """Adapter for metadata from test cases and test steps. Only 'get_taskid()'
    is mandatory."""

    def get_logs(self):
        """Return list of URL's with log data or recorded data."""
        return []

    def get_testcode_info(self):
        """Return informatino about the test case itself (author, requirment,
        modification date, etc)."""
        return TestCodeInfo()

    def get_url(self):
        """Return URL to the test result."""
        pass


class TestStepDataAdapter(TestCaseDataAdapter):
    """Test steps contain the same metadata as test cases."""
    pass



# Observers that add meta data using adapters. ==========================={{{1
class TestSuiteDataObserver(Observer):
    """Copy data from the adapter to the TestSuite object."""

    def __init__(self, adapter):
        self.adapter = adapter

    def notify_abort(self, observable):
        # TODO: Do we need to do something here?
        pass

    def notify_start(self, observable):
        """Copy metadata."""
        observable.metadata.product_name = self.adapter.get_product_name() or observable.name
        observable.metadata.product_id = self.adapter.get_product_id() or observable.id
        observable.metadata.execution_info = self.adapter.get_execution_info()
        observable.metadata.testenv_info = self.adapter.get_testenv_info()
        observable.metadata.simulation_info = self.adapter.get_simulation_info()
        observable.metadata.software_info = self.adapter.get_software_info()

    def notify_finish(self, observable, verdict):
        """Copy results, note that the verdict is handled by the test suite!"""
        observable.url = self.adapter.get_url()
        observable.logs = self.adapter.get_logs()


class TestCaseDataObserver(Observer):
    """Copy data from the adapter to the TestCase object."""

    def __init__(self, adapter):
        self.adapter = adapter

    def notify_abort(self, observable):
        # TODO: Decide what to do here.
        pass

    def notify_start(self, observable):
        """Copy metadata."""
        observable.metadata.testcode_info = self.adapter.get_testcode_info()

    def notify_finish(self, observable, verdict):
        """Copy results, note that the verdicdt is handled by the test suite."""
        observable.url = self.adapter.get_url()
        observable.logs = self.adapter.get_logs()


class TestStepDataObserver(TestCaseDataObserver):
    """Copy data from the adapter to the TestStep object."""
    pass


# modeline ==============================================================={{{1
# vim: set fdm=marker:
# eof
