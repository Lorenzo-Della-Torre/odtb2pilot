"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76502
version: 1
title: ReadDTCInformation (19) - reportDTCSnapshotIdentification (03)
purpose: >
    Since Volvo Car Corporation allows for multiple DTCSnapshot records for one DTC, it must be
    possible to read out which DTCSnapshot records a specific DTC has.

description: >
    The ECU shall support the service ReadDTCInformation - reportDTCSnapshotIdentification in all
    sessions where the ECU supports the service ReadDTCInformation.

details: >
    Import script - Inherited from older version of requirement
"""

from e_76502_MAIN_0_19_reportdtcsnapshotidentification_03_83 import run

if __name__ == '__main__':
    run()
