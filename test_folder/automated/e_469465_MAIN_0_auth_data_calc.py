/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



**********************************************************************************/


"""
reqprod: 469465
version: 0
title: Authentication Data calculation
purpose: >
    Define when to calculate the Authentication Data.

description: >
    The Authentication Data shall be calculated when an event is reported and stored
    to non-volatile memory.

details: >
    Implicitly tested script
    Tested implicitly by REQPROD 469461 because we compare CMAC values there as well
"""

import logging
import sys

logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

try:
    from e_469461_MAIN_1_authentication_data_inputs.py import run
except ModuleNotFoundError as err:
    logging.error("The test that is used to test this requirement can't be found: %s found", err)

if __name__ == '__main__':
    run()
