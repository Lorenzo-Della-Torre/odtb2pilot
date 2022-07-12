"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 72185
version: 1
title: Activate Secondary Bootloader routine
purpose: >
    All ECUs must support routines defined for SWDL.

description: >
    Rationale:
    The routine shall be used to activate the Secondary Bootloader after it has been downloaded to
    volatile memory. The ECU shall start executing the secondary bootloader from the memory
    address defined in the data file containing the Secondary Bootloader.

    Req: The Activate Secondary Bootloader routine with routine identifier as specified in the
    table below shall be implemented as defined in Carcom - Global Master Reference
    Database (GMRDB).
    ------------------------------------------------------------
    Description	                                Identifier
    ------------------------------------------------------------
    Activate Secondary Bootloader	               0301
    ------------------------------------------------------------

    •   It shall be possible to execute the control routine with service as specified in
        Ref[LC : VCC - UDS Services - Service 0x31 (RoutineControl) Reqs].
    •   The final positive response message from the Activate Secondary Bootloader routine shall
        be sent when the SBL has been activated, i.e. from the SBL. If the SBL is already
        activated at the time of the request the ECU shall respond with a positive response
        message with Routine Completed = 0.
    •   The routine shall be implemented as a type 1 routine.

    The ECU shall support the identifier in the following sessions:
    •   Programming session (which includes both primary and secondary bootloader)

details: >
    Import script - Inherited from older version of requirement
"""

from e_72185_MAIN_0_activate_sbl_routine import run

if __name__ == '__main__':
    run()
