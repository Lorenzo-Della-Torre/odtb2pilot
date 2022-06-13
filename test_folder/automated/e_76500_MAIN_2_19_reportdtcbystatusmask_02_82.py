"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76500
version: 2
title: ReadDTCInformation (19) - reportDTCByStatusMask (02)
purpose: >
    It shall be possible to read out DTCs with a specific status

description: >
    The ECU shall support the service ReadDTCInformation - reportDTCByStatusMask in all sessions
    where the ECU supports the service ReadDTCInformation.

details: >
    Import script - Inherited from older version of requirement
"""

from e_76500_MAIN_1_19_reportdtcbystatusmask_02_82 import run

if __name__ == '__main__':
    run()
