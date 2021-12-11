"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

"""
version:  1
reqprod:  76421

title:

    ReadMemoryByAddress (23) - memoryAddress (MA)

purpose:

    Compliance with VOLVO CAR CORPORATION tools.

description:

    The ECU shall support the service readMemoryByAddress with the data
    parameter memoryAddress in all sessions where the ECU supports the service
    readMemoryByAddress. The implementer shall define the values of the
    memoryAddress.

details: >

    This testcase has been tested by REQPROD 76173. The data is being read from
    the memory address 0x70000000 in each session using the following payload:
    0x232470000000000A. The last 0x0A corresponds to the 10 bytes of data that
    is requested.

"""

import logging
import sys

logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

logging.info("Testcase result: Tested implicitly by REQPROD 76173")
