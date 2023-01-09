"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76482
version: 1
title: : DynamicallyDefineDataIdentifier (2C) - clearDynamicallyDefinedDataIdentifier (03, 83)
purpose: >
    Standardized clear procedure to have compliance with VOLVO CAR CORPORATION tools

description: >
    The ECU shall support the service dynamicallyDefineDataIdentifier -
    clearDynamicallyDefinedDataIdentifier in all sessions where the ECU supports the service
    dynamicallyDefineDataIdentifier.

details: >
    Implicitly tested script
    Tested implicitly by REQPROD 76485 because both the requirements check that the ECU shall
    support the service dynamicallyDefineDataIdentifier - clearDynamicallyDefinedDataIdentifier
"""
import logging
import sys
from\
e_76485_MAIN_2_dynamically_define_data_identifier_2c_clear_of_dynamically_define_data_identifier\
import run

logging.basicConfig(format=' %(message)s',stream=sys.stdout, level=logging.INFO)


if __name__ == '__main__':
    run()
