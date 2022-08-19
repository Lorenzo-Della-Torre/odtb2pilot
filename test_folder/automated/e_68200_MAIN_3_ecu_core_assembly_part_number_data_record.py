"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 68200
version: 3
title: ECU Core Assembly Part Number data record
purpose: >
    To enable readout of a part number that identifies the combination of the ECU hardware and any
    non-replaceable software (bootloaders and other fixed software).

description: >
    A data record with identifier as specified in the table below shall be implemented exactly as
    defined in Carcom - Global Master Reference Database

    Description	                                Identifier
    ---------------------------------------------------------
    ECU Core Assembly Part Number	            F12A
    ---------------------------------------------------------

    •	It shall be possible to read the data record by using the diagnostic service specified in
        Ref[LC : Volvo Car Corporation - UDS Services - Service 0x22 (ReadDataByIdentifier) Reqs].

    The identifier shall be implemented in the following sessions:
        •   Default session
        •   Programming session (which includes both primary and secondary bootloader)
        •   Extended Session

details: >
    Import script - Inherited from older version of requirement
"""

from e_68200_MAIN_2_ecu_core_assembly_part_number_data_record import run

if __name__ == '__main__':
    run()
