"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76503
version: 2
title: ReadDTCInformation (19) - reportDTCSnapshotRecordByDTCNumber (04)
purpose: >
    Snapshot of data values shall be stored along with the DTC when the criteria is fulfilled in
    order for sampling a snapshot. This snapshot data shall be possible to read out.

description: >
    The ECU shall support the service ReadDTCInformation - reportDTCSnapshotRecordByDTCNumber
    in all sessions where the ECU supports the service ReadDTCInformation.

details: >
    Import script - Inherited from older version of requirement
"""

from e_76503_MAIN_1_19_reportdtcsnapshotrecordbydtcnumber_04_84 import run

if __name__ == '__main__':
    run()
