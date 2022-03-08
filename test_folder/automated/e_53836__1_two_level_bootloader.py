"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 53836
version: 1
title: Two level bootloader
purpose: >
    For security and data integrity purpose the ECU shall support two levels of
    bootloaders, PBL and SBL.

description: >
    An ECU shall support the software download concept by the use of two bootloaders; primary- and
    secondary bootloader.

details: >
    Implicitly tested script
    Tested implicitly by REQPROD 400425 because software part number is tested with software
    download principle.
"""

import logging
import sys

logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

try:
    from e_400425_MAIN_2_programming_of_logical_blocks.py import run
except ModuleNotFoundError as err:
    logging.error("The test that is used to test this requirement can't be found: %s found", err)

if __name__ == '__main__':
    run()
