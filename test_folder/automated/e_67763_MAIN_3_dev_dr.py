"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 67763
version: 3
title: Development specific data records - implementer specified
purpose: >
	ECU Specific data records are not supported by Volvo Car Corporation tools and must be
    defined in a separate identifier range.

description: >
    If data records that are needed only during the development of the ECU are defined by the
    implementer, these data records shall have data identifiers in the ranges as specified in
    the table below:
    ------------------------------------------------------------------------------------------
    Description                                                          Identifier range
    ------------------------------------------------------------------------------------------
    Development specific data records - Implementer specified             D900 - DCFF
                                                                          E300 - E4FF
                                                                          EE00 - EFFF
    ------------------------------------------------------------------------------------------
    • It shall be possible to read the data record by using the diagnostic service specified in
      Ref[LC : Volvo Car Corporation - UDS Services -Service 0x22 (ReadDataByIdentifier) Reqs]

details: >
    Import script - Inherited from older version of requirement
"""

from e_67763_MAIN_2_dev_dr import run

if __name__ == '__main__':
    run()
