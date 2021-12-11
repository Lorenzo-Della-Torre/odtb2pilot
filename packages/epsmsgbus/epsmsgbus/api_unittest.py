"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

"""
Experimental API for implementation of message bus handling together with
Python's unittest module.
"""

import unittest

import epsmsgbus.api as api


# class TestSuite(unittest.TestSuite):
#     def run(self, *a, **k):
#         print("STARTED Test Suite", self._tests)
#         testsuite_started(self, self.__class__.__name__)
#         try:
#             super(TestSuite, self).run(*a, **k)
#         finally:
#             print("FINISHED Test Suite", self._tests)
#             testsuite_finished(self, 'executed')
#
# unittest.TestLoader.suiteClass = TestSuite


class TestCase(unittest.TestCase):
    def setUp(self):
        super(TestCase, self).setUp()
        api.testcase_started(TestCaseDataAdapter(), self.__class__.__name__)

    def tearDown(self):
        super(TestCase, self).tearDown()
        api.testcase_ended('passed')


class TestSuiteDataAdapter(api.TestSuiteDataAdapter):
    """TestSuite data, note that this may need to be extended."""
    def get_execution_info(self):
        return api.ExecutionInfo()

    def get_simulation_info(self):
        return api.SimulationInfo()

    def get_software_info(self):
        return api.SoftwareInfo()

    def get_testenv_info(self):
        return api.TestEnvironmentinfo()

    def get_logs(self):
        return []

    def get_url(self):
        pass


class TestCaseDataAdapter(api.TestCaseDataAdapter):
    """TestCase data."""
    def get_testcode_info(self):
        return api.TestCodeInfo()

    def get_url(self):
        pass

    def get_logs(self):
        return []


# TODO: Find out a way to let each assertion be a test step!!


# Sample test case ======================================================={{{1
class TheTestCase(TestCase):
    # THis is the dummy test case
    def test_01(self):
        self.assertEqual('a', 'a')
        self.assertEqual('a', 'b')


# Sample ================================================================={{{1
if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    try:
        # Dont save to database, just send to Cynosure. Modify if needed.
        api.messagehandler(use_mq=True, use_db=False)
        api.testsuite_started(TestSuiteDataAdapter(), 'UnittestSample')
        mod = unittest.main(exit=False)
    finally:
        result = 'unknown'
        if len(mod.result.errors) > 0:
            result = 'errored'
        elif len(mod.result.failures) > 0:
            result = 'failed'
        elif mod.result.wasSuccessful():
            result = 'passed'
        api.testsuite_ended(result)


# eof
