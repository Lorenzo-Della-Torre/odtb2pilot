"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/


reqprod: 76170
version: 2
title: : ReadDataByIdentifier (22) - dataIdentifier(-s)

purpose: >
    It shall be possible to read data from all ECUs

description: >
    The ECU shall support the service readDataByIdentifer with the data parameter
    dataIdentifier(-s). The ECU shall implement the service accordingly:

    Supported sessions:
    The ECU shall support Service readDataByIdentifer in:
    •	defaultSession
    •	extendedDiagnosticSession
    •	programmingSession, both primary and secondary bootloader

    Response time:
    Maximum response time for the service readDataByIdentifier (0x22) is 200 ms.
    Effect on the ECU normal operation:
    The service readDataByIdentifier (0x22) shall not affect the ECUs ability to
    execute non-diagnostic tasks.

    Entry conditions:
    The ECU shall not implement entry conditions for service readDataByIdentifier (0x22).

    Security access:
    The ECU are allowed to protect the service ReadDataByIdentifier (0x22), read by other
    than system supplier specific dataIdentifiers, by using the service securityAccess (0x27)
    only if approved by Volvo Car Corporation.

details: >
    Import script - Inherited from older version of requirement
"""

from e_76170_MAIN_1_service_22_dids import run

if __name__ == '__main__':
    run()
