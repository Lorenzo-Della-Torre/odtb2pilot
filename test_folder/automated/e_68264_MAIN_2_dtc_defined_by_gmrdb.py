"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 68264
version: 1
title: DTCs defined by GMRDB
purpose: >
	All DTC information shall be supported by VCC tools and must therefore be defined in GMRDB.

description: >
    Rationale-
    Global Master Reference Data Base (GMRDB) is a part of the central diagnostic database that
    is used by Volvo Car Corporation in order to document the implementation of diagnostics in the
    ECUs. GMRDB is a library containing predefined DTCs, DIDs and Control Routines. The definition
    of DTCs (both identifier and description) that are supposed to be used by Volvo tools must
    have its origin in GMRDB. GMRDB holds only the 2-byte base DTC.

    Requirement-
    DTCs supported by an ECU shall be implemented in accordance to the definition in Global Master
    Reference Database. Development specific implementer specified DTCs are excluded from this
    requirement.

details: >
    Import script - Inherited from older version of requirement
"""

from e_68264_MAIN_1_dtc_defined_by_gmrdb import run

if __name__ == '__main__':
    run()
