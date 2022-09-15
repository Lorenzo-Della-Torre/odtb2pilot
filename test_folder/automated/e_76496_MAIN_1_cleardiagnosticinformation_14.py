"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76496
version: 1
title: ClearDiagnosticInformation (14)
purpose: >
    It shall be possible to erase DTCs and DTC related information

description: >
    The ECU must support the service ClearDiagnosticInformation. The ECU shall implement the
    service accordingly:

    Supported sessions:
    The ECU shall support Service ClearDiagnosticInformation in:
        •	defaultSession
        •	extendedDiagnosticSession
    The ECU may, but are not required to, support clearDiagnosticInformation in programmingSession

    Response time:
    Maximum response time for the service ClearDiagnosticInformation (0x14) is 3500ms.

    Effect on the ECU normal operation:
    The service ClearDiagnosticInformation (0x14) shall not affect the ECU's ability to execute
    non-diagnostic tasks.

    Entry conditions:
    If the ECU implement safety requirements with an ASIL higher than QM it shall, in all
    situations when diagnostic services may violate any of those safety requirements, reject the
    critical diagnostic service requests. Note that if the ECU rejects such critical diagnostic
    service requests, this requires an approval by Volvo Car Corporation.

    Security access:
    The ECU shall not protect service ClearDiagnosticInformation by using the service
    securityAccess (0x27).

details: >
    Import script - Inherited from older version of requirement
"""

from e_76496_MAIN_0_cleardiagnosticinformation_14 import run

if __name__ == '__main__':
    run()
