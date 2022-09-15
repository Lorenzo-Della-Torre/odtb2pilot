"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/


reqprod: 76139
version: 4
title: : ECUReset (11)

purpose: >
    ECU reset is used in the SWDL process and may be useful when testing an ECU

description: >
    The ECU must support the service ECUReset. The ECU shall implement the service accordingly.

    Supported sessions-
    The ECU shall support Service ECUReset in
    •	defaultSession
    •	extendedDiagnosticSession
    •	programmingSession, both primary and secondary bootloader
    Response time-
    Maximum response time for the service ECUReset (0x11) is P2Server_max.

    Effect on the ECU normal operation-
    The service ECUReset (0x11) is allowed to affect the ECUs ability to execute non-diagnostic
    tasks. The service is only allowed to affect execution of the non-diagnostic tasks during
    the execution of the diagnostic service.

    After the diagnostic service is completed any effect on the non-diagnostic tasks is not
    allowed anymore (normal operational functionality resumes).

    Entry conditions-
    Entry conditions for service ECUReset (0x11) are allowed only if approved by Volvo Car
    Corporation.
    If the ECU implement safety requirements with an ASIL higher than QM it shall, in all
    situations when diagnostic services may violate any of those safety requirements, reject
    the critical diagnostic service requests. Note that if the ECU rejects such critical
    diagnostic service requests, this requires an approval by Volvo Car Corporation.

    Security access-
    The ECU shall not protect service ECUReset by using the service securityAccess (0x27).


details: >
    Import script - Inherited from older version of requirement
"""

from e_76139_MAIN_3_ecureset__11_ import run

if __name__ == '__main__':
    run()
