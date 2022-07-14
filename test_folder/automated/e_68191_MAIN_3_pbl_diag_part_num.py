"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.


/*********************************************************************************/

reqprod: 68191
version: 3
title: Primary Bootloader Diagnostic Database Part Number
purpose: >
    To enable readout of a database key for the diagnostic database used by the ECU's primary
    bootloader SW.

description: >
    The data record Primary Bootloader Diagnostic Database Part Number with identifier as specified
    in the table below shall be implemented exactly as defined in Carcom - Global Master Reference
    Database (GMRDB).

    Description	                                                Identifier
    --------------------------------------------------------------------------
    Primary Bootloader Diagnostic Database Part Number	          F121
    --------------------------------------------------------------------------

    •   It shall be possible to read the data record by using the diagnostic service specified
        in Ref[LC : Volvo Car Corporation - UDS Services - Service 0x22 (ReadDataByIdentifier)
        Reqs].
    •   It is allowed to change the value of the data record one time in secondary bootloader by
        diagnostic service as specified in Ref[LC : VCC - UDS Services - Service 0x2E
        (WriteDataByIdentifier) Reqs].

    The ECU shall support the identifier in the following sessions:
    •   Programming session (which includes both primary and secondary bootloader)

details: >
    Import script - Inherited from older version of requirement
"""

from e_68191_MAIN_2_pbl_diag_part_num import run

if __name__ == '__main__':
    run()
