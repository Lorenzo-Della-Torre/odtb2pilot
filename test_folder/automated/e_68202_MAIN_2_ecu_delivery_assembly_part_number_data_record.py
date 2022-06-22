"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 68202
version: 2
title: ECU Delivery Assembly Part Number data record
purpose: >
    To enable readout of a part number that identifies the complete ECU at the point of delivery
    to the assembly plant.

description: >
    A data record with identifier as specified in the table below shall be implemented exactly as
    defined in Carcom - Global Master Reference Database.

    Description                         	Identifier
    ECU Delivery Assembly Part Number	    F12B

    •	It shall be possible to read the data record by using the diagnostic service specified in
        Ref[LC : Volvo Car Corporation - UDS Services - Service 0x22 (ReadDataByIdentifier) Reqs].

    The identifier shall be implemented in the following sessions:
    •	Default session
    •	Programming session (which includes both primary and secondary bootloader)
    •	Extended session

details: >
    Import script - Inherited from older version of requirement
"""

from e_68202_MAIN_1_ecu_delivery_assembly_part_number_data_record import run

if __name__ == '__main__':
    run()
