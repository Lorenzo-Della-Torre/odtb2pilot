"""
analytics test cases

make sure that these tests never writes to production db
"""
from supportfunctions import analytics

def test_testcase_has_started():
    """analytics test case """
    assert analytics.lack_testcases()
    analytics.testsuite_started()
    assert analytics.lack_testcases()
    analytics.testcase_started("first")
    assert not analytics.lack_testcases()
    analytics.testcase_ended("passed")
    analytics.testsuite_ended()
    assert analytics.lack_testcases()
