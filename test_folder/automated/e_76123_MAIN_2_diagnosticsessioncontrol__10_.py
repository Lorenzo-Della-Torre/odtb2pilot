"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76123
version: 2
title: : DiagnosticSessionControl (10)
purpose: >

description: >
    The ECU must support the service diagnosticSessionControl. The ECU shall implement the service
    accordingly:

    Supported session:
    The ECU shall support Service diagnosticSessionControl in:
    •	defaultSession
    •	extendedDiagnosticSession
    •	programmingSession, both primary and secondary bootloader

    Response time:
    Maximum response time for the service diagnosticSessionControl (0x10) is P2Server_max.

    Effect on the ECU normal operation, programmingSession:
    Transition from and to programmingSession is allowed to affect the ECUs ability to execute
    tasks that are non-diagnostic. The service is only allowed to affect execution of the
    non-diagnostic tasks during the execution of the diagnostic service. After the diagnostic
    service is completed any effect on the non-diagnostic tasks is not allowed anymore
    (normal operational functionality resumes).

    Effect on the ECU normal operation, other sessions than programmingSession:
    All other transitions than from and to programmingSession (excluding programmingSession to
    programmingSession) shall not affect the ECUs ability to execute non-diagnostic tasks.

    Entry conditions, programmingSession:
    Entry conditions for service diagnosticSessionConrol (0x10), changing to programmingSession
    (0x02) (excluding programmingSession to programmingSession):
    The implementer shall implement the ECUs condition for entering programmingSession based on
    the allocated functionality. The condition shall ensure a defined and safe vehicle state when
    entering programmingSession and must at a minimum include vehicle speed < 3km/h and usage
    mode ≠ Driving (if not otherwise approved Volvo Car Corporation).
    In an impaired vehicle or in a stand-alone scenario if the vehicle signal(s) used in the
    evaluation of the condition e.g. speed and/or "main propulsion system not active" is
    unavailable shall the safety mechanism not prevent the ECU to change to programmingSession
    to allow SWDL.
    If the ECU implement safety requirements with an ASIL higher than QM it shall, in all
    situations when diagnostic services may violate any of those safety requirements, reject the
    critical diagnostic service requests. Note that if the ECU rejects such critical diagnostic
    service requests, this requires an approval by Volvo Car Corporation.

    Entry conditions, other sessions than programmingSession:
    The ECU shall not implement entry conditions for service diagnosticSessionConrol (0x10) in
    other session transitions than changing to programmingSession (0x02).

    Security access:
    The ECU shall not protect service diagnosticSessionControl by using the service securityAccess
    (0x27).

details:
    Verify ECU should remain in default session after getting session change request to programming
    while vehicle is moving

    Import script - Inherited from older version of requirement
"""

from e_76123_MAIN_1_diagnosticsessioncontrol__10_ import run

if __name__ == '__main__':
    run()
