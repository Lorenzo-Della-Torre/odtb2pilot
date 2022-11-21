"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76141
version: 2
title: SecurityAccess (27)
purpose: >
    Define availability of SecurityAccess service

description: >
    The ECU shall implement SecurityAccess (0x27) service accordingly:

    Supported session:
        • SecurityAccess shall not be supported in the defaultSession.
        • The services securityAccess requestSeed 0x01 and sendKey 0x02 shall only be supported
          in programmingSession, both primary and secondary bootloader.
        • The services securityAccess requestSeed in the range 0x03-0x41and sendKey in the
          range 0x04-0x42 may be supported by the ECU but only in the extendedDiagnosticSession.

    SecurityAccess algorithm:

    The requestSeed range 0x01-0x41 and corresponding sendKey range 0x02-0x42 shall use the
    standardized SecurityAccess algorithm specified by Volvo Car Corporation.The requestSeed range
    0x61-0x7E and corresponding sendKey range 0x62-0x7F are not allowed to use the standardized
    SecurityAccess algorithm specified by Volvo Car Corporation but shall use another
    SecurityAccess algorithm provided by the implementer. The number of bytes of the data parameter
    securityKey is specified by the implementer. Note that VCC tools are not required to support
    the range.

    P4Server_max response time:
    Maximum response time for the service securityAccess (0x27) is P2Server_max.

    Effect on the ECU operation:
    The service securityAccess (0x27) shall not affect the ECU's ability to execute non-diagnostic
    tasks.

    Entry conditions:
    Entry conditions for service SecurityAccess (0x27) are not allowed.

details: >
    Import script - Inherited from older version of requirement
"""

from e_76141_MAIN_1_security_access_27 import run

if __name__ == '__main__':
    run()
