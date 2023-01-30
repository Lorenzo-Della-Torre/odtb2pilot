"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 401140
version: 3
title: Complete&Compatible - Definition of being Compatible
purpose: >
    The purpose with the compatibility validation is to detect if present softwares are compatible
    in such way that the ECU is able to start and communicate. Hence, the ECU application could
    inform the user by e.g. setting a diagnostic trouble code.

description: >
    The ECU is compatible if it is at least able to start the application, is able to respond to
    diagnostics and alert the user if a function is disabled or degraded. An ECU that is
    compatible shall always be able to enter Programming Session and be re-programmed.
    Note: The application must react accordingly, i.e. enter a defined fail-safe mode if it is
    started but a function is disabled or degraded. Such a behavior is however the responsibility
    of the application to decide

details: >
    Implicitly tested script
    Tested implicitly by REQPROD 52282 because it verifies that an ECU that is compatible shall
    always be able to enter programming session and be re-programmed.
"""

import logging
import sys
from e_52282__2_complete_and_compatible_function import run

logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

if __name__ == '__main__':
    run()
