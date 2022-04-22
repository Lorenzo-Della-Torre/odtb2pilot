"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 74107
version: 3
title: ECU ability to receive requests
purpose: >
    Define a time the ECU is allowed to be unavailable in regards of diagnostic communication
    when powering up and the time shall be short enough to not be a problem for manufacturing
    and aftersales.

description: >
    The ECU shall all the time be able to receive diagnostic service requests and send a response
    (positive or negative) on the requests as long as the ECU is within an operation cycle.

details: >
    Implicitly tested script
    Tested implicitly by REQPROD 391192 because responses(positive and negative) are verified
    after ecu reset and after 2500ms since ecu reset .
"""

import logging
import sys

logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

try:
    from e_391192_MAIN_2_ECU_start_up_time import run
except ModuleNotFoundError as err:
    logging.error("The test that is used to test this requirement can't be found: %s found", err)

if __name__ == '__main__':
    run()
