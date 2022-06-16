"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 68225
version: 3
title: Primary Bootloader Software Part Number data record
purpose: >
    To enable readout of the part number of the Primary Bootloader SW

description: >
    A data record with identifier as specified in the table below shall be implemented exactly as
    defined in Carcom - Global Master Reference Database (GMRDB).
    --------------------------------------------------------------------------------------------
                Description	                                       Identifier
    --------------------------------------------------------------------------------------------
    Primary Bootloader Software Part Number data record	              F125
    --------------------------------------------------------------------------------------------

    •	It shall be possible to read the data record by using the diagnostic service specified in
        Ref[LC : Volvo Car Corporation - UDS Services - Service 0x22 (ReadDataByIdentifier) Reqs].

    •	It is allowed to change the value of the data record one time in secondary bootloader by
        diagnostic service as specified in Ref[LC : VCC - UDS Services - Service 0x2E
        (WriteDataByIdentifier) Reqs].

    The ECU shall support the identifier in the following sessions:
    •	Programming session (which includes both primary and secondary bootloader)

details: >
    Import script - Inherited from older version of requirement
"""

from e_68225_MAIN_2_pbl_sw_part_num import run

if __name__ == '__main__':
    run()
