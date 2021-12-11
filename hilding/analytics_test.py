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
analytics test cases

do make sure that these tests never writes to production db
"""
from hilding import analytics

def _test_testcase_has_started():
    """analytics test case """
    assert analytics.lack_testcases()
    analytics.testsuite_started()
    assert analytics.lack_testcases()
    analytics.testcase_started("first")
    assert not analytics.lack_testcases()
    analytics.testcase_ended("passed")
    analytics.testsuite_ended()
    assert analytics.lack_testcases()

def _test_suite():
    """make sure the test suite runs well"""
    analytics.testsuite_started()
    analytics.testcase_started("case1")
    analytics.teststep_started("step1")
    analytics.teststep_ended("passed")
    analytics.testcase_ended("passed")
    analytics.testsuite_ended()

def _test_suite_dubble_teststep_ended():
    analytics.testsuite_started()
    analytics.testcase_started("case1")
    analytics.teststep_started("step1")
    analytics.teststep_ended("passed")
    analytics.teststep_ended("passed")
    analytics.testcase_ended("passed")
    analytics.testsuite_ended()

def _test_suite_without_steps():
    analytics.testsuite_started()
    analytics.testcase_started("case1")
    analytics.testcase_ended("passed")
    analytics.testsuite_ended()
