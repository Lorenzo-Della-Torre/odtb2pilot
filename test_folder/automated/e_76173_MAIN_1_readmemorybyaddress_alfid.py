"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76173
version: 1
title: ReadMemoryByAddress (23) - addressAndLengthFormatIdentifier (ALFID)
purpose: >
	To make it easier for VOLVO CAR CORPORATION tools, the ECU shall support standardized request

description: >
    The ECU shall support the service readMemoryByAddress with the data parameter
    addressAndLengthFormatIdentifier set to one of the following values:
    •	0x14
    •	0x24

    The ECU shall support the data parameter in all sessions where the ECU supports the service
    readMemoryByAddress

details: >
    Import script - Inherited from older version of requirement
"""

from e_76173_MAIN_0_readmemorybyaddress_alfid import run

if __name__ == '__main__':
    run()
