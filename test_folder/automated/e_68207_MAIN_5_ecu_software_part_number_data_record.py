"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 68207
version: 5
title: ECU Software Part Number data record
purpose: >
    To enable readout of the part number for the ECU software

description: >
    A data record with identifier 0xF12E shall be implemented. The data records shall be
    implemented exactly as defined in Carcom - Global Master Reference Database.

    The content of the data record (0xF12E) with the data identifier shall be the following:
    --------------------------------------------------------------------------------
            Byte                          Description
    --------------------------------------------------------------------------------
            #1                     Total number of ECU Software Part Numbers
            #2-8                   ECU Software #1 Part Number
            #9-15                  ECU Software #2 Part Number
              .
              .
            #N-(N+6)               ECU Software #X Part Number
    --------------------------------------------------------------------------------

    The Part Number(s) is only allowed to be used for item(s) that can be separately downloaded to
    the ECU.
    • It shall be possible to read the data record by using the diagnostic service specified in
    Ref[LC : Volvo Car Corporation - UDS Services - Service 0x22 (ReadDataByIdentifier) Reqs].

    The identifier shall be implemented in the following sessions:
    • Default session
    • Extended Session

details: >
    Import script - Inherited from older version of requirement
"""

from e_68207_MAIN_4_ecu_software_part_number_data_record import run

if __name__ == '__main__':
    run()
