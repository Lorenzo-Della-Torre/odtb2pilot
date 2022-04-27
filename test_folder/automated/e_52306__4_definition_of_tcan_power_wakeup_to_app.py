"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 52306
version: 4
title: Definition of TCANPowerWakeUpToApp
purpose: >
    To define maximum time to start communication.

description: >
    TCANPowerWakeUpToApp shall be equal to 150 ms.
    If another requirement define this time to be shorter that requirement
    shall override this requirement.

details: >
    Implicitly tested script
    Tested implicitly by REQPROD 52307 because timing at power up or reset initialization CAN
    contains definition of TCANPowerWakeUpToApp
"""
import logging
import sys
from e_52307__3_timing_at_power_up_or_reset_initialization_can import run

logging.basicConfig(format=' %(message)s',stream=sys.stdout, level=logging.INFO)


if __name__ == '__main__':
    run()
