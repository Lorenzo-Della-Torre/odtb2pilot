"""

/*********************************************************************************/



Copyright © 2023 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 56151
version: 2
title: P2Server_max - non programming session
purpose: >
    P2Server_max is the maximum time for the server to start with the response message after
    the reception of a request message.

description:
    The maximum time for P2Server in all sessions except programmingSession is 50ms.

details:
    Implicitly tested by:
        REQPROD 76172 ReadMemoryByAddress (Service 23).
"""
import sys
import logging
from e_76172_MAIN_0_readmemorybyaddress_s23 import run

logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)


if __name__ == '__main__':
    run()
