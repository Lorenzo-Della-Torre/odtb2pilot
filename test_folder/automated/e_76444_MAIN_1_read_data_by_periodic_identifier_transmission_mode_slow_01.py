"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76444
version: 1
title: ReadDataByPeriodicIdentifier (2A) - transmissionMode slow (01)
purpose: >
    Define the transmissionMode slow

description: >
    The ECU may support the service readDataByPeriodicIdentifier with the data parameter
    transmissionMode slow in all sessions where the ECU supports the service
    readDataByPeriodicIdentifier. The implementer defines the value of the transmission rate
    in the transmissionMode slow.

details: >
    Implicitly tested script
    Tested implicitly by REQPROD 76442 because the transmissionMode slow (0x01) parameter has
    already verified in the requirement 76442
"""
import logging
import sys

logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

try:
    from e_76442_MAIN_2_read_data_by_periodic_identifier_2a.py import run
except ModuleNotFoundError as err:
    logging.error("The test that is used to test this requirement can't be found: %s found", err)

if __name__ == '__main__':
    run()
