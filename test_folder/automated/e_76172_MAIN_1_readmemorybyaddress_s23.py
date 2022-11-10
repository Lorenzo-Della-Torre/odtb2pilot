"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76172
version: 1
title: ReadMemoryByAddress (23)
purpose: >
    ReadMemoryByAddress shall primarily be used during development or for validation data written
    by WriteMemoryByAddress.

description: >
    The ECU shall support the service ReadMemoryByAddress if the ECU is involved in propulsion or
    safety functions in the vehicle. Otherwise, the ECU may support the service
    ReadMemoryByAddress. If implemented, the ECU shall implement the service accordingly:

    Supported sessions:
    The ECU shall support Service ReadMemoryByAddress in:
        • defaultSession
        • extendedDiagnosticSession
    The ECU shall not support service ReadMemoryByAddress in programmingSession.

    Response time:
    Maximum response time for the service ReadMemoryByAddress (0x23) is P2Server_max.

    Effect on the ECU normal operation:
    The service ReadMemoryByAddress (0x23) shall not affect the ECU's ability to execute
    non-diagnostic tasks.

    Entry conditions:
    The ECU shall not implement entry conditions for service ReadMemoryByAddress (0x23).

    Security access:
    The ECU may protect service ReadMemoryByAddress by using the service securityAccess (0x27). At
    least shall memory areas, which are included as data parameters in a dataIdentifier, have the
    same level of security access protection as for reading with service ReadDataByIdentifier(0x22).

details: >
    Import script - Inherited from older version of requirement
"""

from e_76172_MAIN_0_readmemorybyaddress_s23 import run

if __name__ == '__main__':
    run()
