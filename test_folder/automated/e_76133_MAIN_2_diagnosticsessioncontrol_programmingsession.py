"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76133
version: 2
title: DiagnosticSessionControl(10) programmingSession (02, 82)
purpose: >
	It shall be possible to re-program any ECU on the public network.

description: >
	The ECU shall support the service diagnosticSessionControl - programmingSession in:
    •	defaultSession
    •	extendedDiagnosticSession
    •	programmingSession, both primary and secondary bootloader.

details: >
    Import script - Inherited from older version of requirement
"""

from e_76133_MAIN_1_diagnosticsessioncontrol_programmingsession import run

if __name__ == '__main__':
    run()
