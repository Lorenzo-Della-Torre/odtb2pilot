/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



**********************************************************************************/


"""
This is a sample that shows how to use the API for message bus and database.
"""

import logging
import epsmsgbus


class MyTestSuiteDataAdapter(epsmsgbus.TestSuiteDataAdapter):
    """Sample adapter where all fields are filled in."""
    def __init__(self, name='Regression Test Suite', identifier='1.0.0', jobid='J12'):
        self.name = name
        self.id = identifier
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
                description='Sample test suite for demo purposes.',
                executor='Donald Duck')

    def get_simulation_info(self):
        """Return information about the virtual simulation model running on the
        HIL simulator."""
        return epsmsgbus.SimulationInfo(
                build_id='SCLX_V331_BECM_PP_2020w35_1B1eFKm',
                project='V331',
                branch='PP',
                ecu='BECM',
                dbc='SPA3310_ConfigurationsCMAVolvo2_Front3CANCfg_190208_Prototype')

    def get_software_info(self):
        """Return information about the software under test."""
        return epsmsgbus.SoftwareInfo(
                ecu='BECM',
                platform='V331',
                vehicle_project='CMA',
                vehicle_series='PP',
                version='5.4',
                githash='c70592cbc8eac2c5f50ee18c85779f9c0757e741',
                changeset='7815',
                inhousechangeset='7733')

    def get_testenv_info(self):
        """Return information about the test environment."""
        return epsmsgbus.TestEnvironmentinfo(
                name='HIL 91',
                description='Dynamic domain HIL for future projects.',
                platform='HyperXperience')

    def get_logs(self):
        """Return list of URL's to optional log files or recorded data."""
        return [
            'http://the.url.to.me/results/testsuite/31411/log.txt',
            'http://the.url.to.me/results/testsuite/31411/recording.mf4',
            'http://the.url.to.me/results/testsuite/31411/inputdata.json',
        ]

    def get_url(self):
        """Return URL to the test report."""
        return 'http://the.url.to.me/results/testsuite/31411/report.pdf'


class MyTestCaseDataAdapter(epsmsgbus.TestCaseDataAdapter):
    """Adapter for metadata from test cases and test steps. Only 'get_taskid()'
    is mandatory."""
    def __init__(self, name):
        self.name = name

    # OPTIONAL fields ----------------------------------------------------{{{3
    def get_logs(self):
        """Return list of URL's with log data or recorded data."""
        return [
            'http://the.url.to.me/results/testsuite/31411/%s/log.txt' % self.name,
            'http://the.url.to.me/results/testsuite/31411/%s/recording.mf4' % self.name,
            'http://the.url.to.me/results/testsuite/31411/%s/inputdata.json' % self.name,
        ]

    def get_testcode_info(self):
        """Return informatino about the test case itself (author, requirment,
        modification date, etc)."""
        import datetime, random
        description = random.choice((
                'Important safety functions',
                'Whatever we like',
                'Something useful'))
        reqnr = random.choice(('444444', '9191991', '650110', '000001', '314151', '271828'))
        return epsmsgbus.TestCodeInfo(
                author='facosta',
                description=description,
                creationdate=datetime.datetime(2015, 12, 31, 0, 10),
                modificationdate=datetime.datetime.utcnow(),
                requirement='REQPROD %s/main/2' % reqnr,
                responsible='Ricardo Izecson dos Santos Leite (97660) +46 728 889303')

    def get_url(self):
        """Return URL to the test result."""
        return 'http://the.url.to.me/results/testsuite/31411/%s/report.pdf' % self.name


class MyTestStepDataAdapter(epsmsgbus.TestStepDataAdapter):
    def get_testcode_info(self):
        # No requirement info on test step level
        import datetime
        return epsmsgbus.TestCodeInfo(
                author='facosta',
                description='Fill in more information here...',
                creationdate=datetime.datetime(2015, 12, 31, 0, 10),
                modificationdate=datetime.datetime.utcnow())


# Just for convenience
def testsuite_started():
    """Signal that test suite started. Link adapter and API function."""
    adapter = MyTestSuiteDataAdapter()
    epsmsgbus.testsuite_started(adapter, adapter.name)


def testsuite_ended():
    """Signal that test suite ended. Link adapter and API function."""
    # No verdict = use the worst verdict of the test cases
    epsmsgbus.testsuite_ended()


def testcase_started(name):
    """Signal that test case ended. Link adapter and API function."""
    adapter = MyTestCaseDataAdapter(name)
    epsmsgbus.testcase_started(adapter, name)


def testcase_ended(verdict):
    """Signal that test case ended. Link adapter and API function."""
    epsmsgbus.testcase_ended(verdict)


def teststep_started(name):
    """Signal that test step started. Link adapter and API function."""
    adapter = MyTestStepDataAdapter()
    epsmsgbus.teststep_started(adapter, name)


def teststep_ended(verdict):
    """Signal that test step ended. Link adapter and API function."""
    epsmsgbus.teststep_ended(verdict)


def main():
    """
    Run a sample test suite with some mock results.
    """
    # Configure to *not* save to the database, and to publish data in Cynosure
    epsmsgbus.messagehandler(use_db=True, use_mq=True)
    # Start test suite with three test cases
    testsuite_started()

    testcase_started('TestCase1-Init')
    teststep_started('Step 1 - download SW')
    teststep_ended('passed')
    teststep_started('Step 2 - check part numbers')
    teststep_ended('passed')
    testcase_ended('passed')

    testcase_started('TestCase2-Diagnostics')
    teststep_started('Step 1 - Clear DTCs')
    teststep_ended('passed')
    teststep_started('Step 2 - Inject fault')
    teststep_ended('passed')
    teststep_started('Step 3 - Check DTCs')
    teststep_ended('passed')
    teststep_started('Step 4 - Remove fault')
    teststep_ended('passed')
    teststep_started('Step 5 - Check DTCs')
    teststep_ended('failed')
    testcase_ended('failed')

    testcase_started('TestCase3-Dynamics')
    teststep_started('Step 1 - Check responsivity')
    teststep_ended('passed')
    teststep_started('Step 2 - Thermal aspects')
    teststep_ended('passed')
    teststep_started('Step 3 - Reflux test')
    teststep_ended('errored')
    testcase_ended('errored')

    testsuite_ended()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    if __name__ == '__main__':
        main()

