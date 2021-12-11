"""
Unit tests for testrunner
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/


"""
import time
from hilding import testrunner

def _test_get_test_res_dir():
    """ make sure two calls to get_test_res_dir gives us the same directory """
    res1 = testrunner.get_test_res_dir("%f")
    time.sleep(0.1)
    res2 = testrunner.get_test_res_dir("%f")
    assert res1 == res2
