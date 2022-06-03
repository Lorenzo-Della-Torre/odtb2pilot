"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76601
version: 2
title: : RoutineControl(31)
purpose: >
    To be able to execute specific functionality in the ECU

description: >
    The ECU shall support the service RoutineControl. The ECU shall implement the service
    accordingly:

    Supported sessions:
    The ECU shall support Service RoutineControl of Routine type 1 - Short routine in:
        •	defaultSession
        •	extendedDiagnosticSession
        •	programmingSession, both primary and secondary bootloader

    The ECU shall support Service RoutineControl of Routine type 2 - Long routine and
    Routine type 3 - Continuous routine in:
        •	extendedDiagnosticSession
        •	programmingSession, both primary and secondary bootloader

    The ECU shall not support Service RoutineControl of Routine type 2 - Long routine and Routine
    type 3 - Continuous routine in defaultSession.

    Response time:
    These are general response timing requirements. Any exceptions from these requirements are
    specified in the requirements for specific control routines.
    Maximum response time for the service RoutineControl (0x31) startRoutine (1),
    Routine type = 1 is 5000ms.
    Maximum response time for the service RoutineControl (0x31) except for startRoutine (1),
    Routine type = 1 is 200 ms.

    Effect on the ECU normal operation:
    The service RoutineControl (0x31) is allowed to affect the ECU's ability to execute
    non-diagnostic tasks. The service is only allowed to affect execution of the non-diagnostic
    tasks during the execution of the diagnostic service. After the diagnostic service is completed
    any effect on the non-diagnostic tasks is not allowed anymore (normal operational functionality
    resumes). The service shall not reset the ECU.

    Entry conditions:
    Entry conditions for service RoutineControl (0x31) are allowed only if approved by Volvo Car
    Corporation.
    If the ECU implement safety requirements with an ASIL higher than QM it shall, in all
    situations when diagnostic services may violate any of those safety requirements, reject the
    critical diagnostic service requests. Note that if the ECU rejects such critical diagnostic
    service requests,this requires an approval by Volvo Car Corporation.

    Security access:
    The ECU may protect the service RoutineControl (0x31) by using the service securityAccess
    (0x27) in other sessions than programmingSession but only if Volvo Car Corporation requires
    or approves it. The ECU is required to protect service RoutineControl (0x31) by service
    securityAccess (0x27) in programmingSession.

details:
    Import script - Inherited from older version of requirement
"""

from e_76601_MAIN_1_rc31 import run

if __name__ == '__main__':
    run()
