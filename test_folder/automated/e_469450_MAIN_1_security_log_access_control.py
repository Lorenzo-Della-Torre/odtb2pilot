"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 469450
version: 1
title: Security Log - Access Control
purpose:
    To prevent unauthorized access to the log, meaning that sensitive information
    about internal processes might be obtained.
description:
    Req:
    Only authorized parties shall be able to view the log data and it must be accessible
    to authorized users when needed, to not reveal e.g. information about the system design
    that might be misused. One of following options shall be applied based on information stored:
    (1) The log data is encrypted according to method agreed with OEM (specifed elsewhere).
    (2) The log data is read (readDataByIdentifier service) protected by using diagnostic service
    securityAccess. Security Access level 0x19 shall be used.
    (3) The log data is not protected with respect to access control. This alternative
    must be used with a motivation/assessment (e.g. the information does not reveal any
    sensitive information).



details:
    Implicitly tested script
    Tested implicitly by REQPROD 469434 because the log data is not protected with respect
    to access control.
"""

import logging
import sys

logging.basicConfig(format=' %(message)s',
                    stream=sys.stdout, level=logging.INFO)

try:
    from e_469434_MAIN_0_minimum_number_of_events_to_be_stored import run
except ModuleNotFoundError as err:
    logging.error(
        "The test that is used to test this requirement can't be found: %s found", err)

if __name__ == '__main__':
    run()
