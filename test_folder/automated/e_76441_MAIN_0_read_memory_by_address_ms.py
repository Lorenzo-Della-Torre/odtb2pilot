"""

/*********************************************************************************/



Copyright © 2023 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

version: 0
reqprod: 76441

title:
    ReadMemoryByAddress (23) - memorySize (MS)

purpose:
    Compliance with VOLVO CAR CORPORATION tools.

description:
    The ECU shall support the service readMemoryByAddress with the data
    parameter memorySize in all sessions where the ECU supports the service
    readMemoryByAddress. The implementer shall define the values of the
    memorySize.

details: >
    Tested implicitly by REQPROD 76173
    This testcase has been tested by REQPROD 76173 where 10 bytes of data is
    set as the memorySize. The data is being read from the memory address
    0x70000000 in each session using the following payload: 0x232470000000000A.
    The last 0x0A corresponds to the 10 bytes of data that is requested.
"""

import logging
import sys

from e_76173_MAIN_0_readmemorybyaddress_alfid import run

logging.basicConfig(format=' %(message)s',stream=sys.stdout, level=logging.INFO)


if __name__ == '__main__':
    run()
