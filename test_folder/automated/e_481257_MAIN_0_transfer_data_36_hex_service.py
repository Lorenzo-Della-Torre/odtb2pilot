"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 481257
version: 0
title: Transfer Data (36 hex) service
purpose: >
    There is a requirement to support the complete vehicle to be re-programmed via a CAN
    interface. Since the maximum message length on a CAN based network is limited to 4 kB the
    diagnostic tester needs to reduce the message length if an ECU (server) is responding with
    a maxNumberOfBlockLength larger than the transport protocol is supporting.

description: >
    The TransferData message length of 3842 bytes (0F02 hex) shall be supported independent if the
    parameter maxNumberOfBlockLenght returned in the RequestDownload service is larger.
    Note: The 3842 bytes is calculated from the formula (n*256) + 2 bytes, where n=15 and the 2
    byte will take the SID and block sequence counter.

details: >
    Implicitly tested script
    Tested implicitly by REQPROD 400425
"""

import logging
import sys
from e_400425_MAIN_2_programming_of_logical_blocks import run

logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

if __name__ == '__main__':
    run()
