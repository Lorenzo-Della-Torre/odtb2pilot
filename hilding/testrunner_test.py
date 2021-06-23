"""
Unit tests for testrunner
"""
import time
from hilding import testrunner

def _test_get_test_res_dir():
    """ make sure two calls to get_test_res_dir gives us the same directory """
    res1 = testrunner.get_test_res_dir("%f")
    time.sleep(0.1)
    res2 = testrunner.get_test_res_dir("%f")
    assert res1 == res2
