"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 67864
version: 3
title: Identification Options-System Supplier Specific data records
purpose: >
    System supplier specific data records are not supported by Volvo Car Corporation tools and must
    be defined in a separate identifier range.

description: >
    If Identification Options data records, that are not for used by Volvo Car Corporation, are
    defined by the system supplier, these data records shall have data identifiers in the range as
    specified in the table below:

    Description	                             Identifier range
    Development specific data records	     F1F0 - F1FF

    •	It may be possible to read the data record by using the diagnostic service specified
        Ref[LC : Volvo Car Corporation - UDS Services -Service 0x22 (ReadDataByIdentifier) Reqs]

details:
    Import script - Inherited from older version of requirement
"""

from e_67864_MAIN_2_id_options_system_supplier_specific_data_records import run

if __name__ == '__main__':
    run()
