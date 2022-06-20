"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 72042
version: 3
title: Support for DTC time stamp #21
purpose: >
    To provide enhanced information about the occurrence of a fault, that may be useful in the
    analysis of the fault.

description: >
    For all DTCs supported by the ECU a data record identified by DTCExtendedDataRecordNumber=21
    shall be implemented according to the following definition:
    •	The record value shall be equal to the global real time (data record 0xDD00) that is taken
        the latest time FDC10 reaches UnconfirmedDTCLimit, since DTC information was last cleared
    •	The time stamp shall only be taken the first time if the FDC10 reaches UnconfirmedDTCLimit
        more than once during an operation cycle.
    •	The stored data record shall be reported as a 4 byte value.

details: >
    Import script - Inherited from older version of requirement
"""

from e_72042_MAIN_3_support_for_dtc_time_stamp_21 import run

if __name__ == '__main__':
    run()
