"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 67761
version: 4
title: Vehicle manufacturer specific data records defined in GMRDB
purpose: >
    Volvo car corporation defines mandatory data records in GMRDB

description: >
    Data records with data identifiers in the ranges as specified in the table below and shall be
    implemented exactly as they are defined in Carcom - Global Master Reference Database.
    ----------------------------------------------------------------------
    Description	                                      Identifier range
    ----------------------------------------------------------------------
    Vehicle manufacturer specific data records	        0100 - D8FF
                                                        DE00 - E2FF
                                                        E600 - ED1F
                                                        ED80 - ED9F
                                                        F010 - F0FF
    ----------------------------------------------------------------------
    It shall be possible to read the data record by using the diagnostic service specified in
    Ref[LC : Volvo Car Corporation - UDS Services -Service 0x22 (ReadDataByIdentifier) Reqs]

details: >
    Import script - Inherited from older version of requirement
"""

from e_67761_MAIN_3_manufacturer_dr import run

if __name__ == '__main__':
    run()
