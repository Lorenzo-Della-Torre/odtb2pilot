"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76132
version: 2
title: DiagnosticSessionControl (10) - defaultSession (01, 81)
purpose: >
    The ECU shall support a method in which the tester can make the ECU revert back to default
    session.

description: >
    The ECU shall support the service diagnosticSessionControl - defaultSession in
    1.	defaultSession
    2.	extendedDiagnosticSession
    3.	programmingSession, both primary and secondary bootloader

details:
    Verify the ECU shall be in default session after reset
    
Import script - Inherited from older version of requirement
"""

from e_76132_MAIN_1_diagnosticsessioncontrol_defaultsession import run

if __name__ == '__main__':
    run()
