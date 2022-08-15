"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 418011
version: 2
title: Check Memory routine
purpose: >
    To initiate the authenticity verification of the downloaded data file at SWDL

description: >
    If the ECU supports software authentication concept as defined in Ref[LC : General Software
    Authentication], the ECU shall implement the Check memory routine with routine identifier as
    specified in the table below. The ECU shall implement the routine exactly as defined in
    Carcom - Global Master Reference Database (GMRDB).

    Description	         Identifier
    Check Memory routine	0212

    It shall be possible to execute the control routine with service as specified in
    Ref[LC : VCC - UDS Services - Service 0x31 RoutineControl Reqs].
    The ECU shall implement the routine as a type 1 routine.
    The response time P4server_max for the Check Memory routine shall be 2000 ms.

    The ECU shall support the identifier in the following sessions
    Programming session (which includes both primary and secondary bootloader)

details: >
    Implicitly tested script
    Tested implicitly by REQPROD 405174
"""

from e_418011_MAIN_1_check_memory_routine import run

if __name__ == '__main__':
    run()
