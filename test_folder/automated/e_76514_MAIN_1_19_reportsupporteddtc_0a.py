"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76514
version: 1
title: ReadDTCInformation (19) - reportSupportedDTC (0A)
purpose: >
    Read out supported DTCs from an ECU

description: >
    The ECU may support the service ReadDTCInformation - reportSupportedDTC in all sessions where
    the ECU supports the service ReadDTCInformation.

details: >
    Import script - Inherited from older version of requirement
"""

from e_76514_MAIN_0_19_reportsupporteddtc_0a import run

if __name__ == '__main__':
    run()
