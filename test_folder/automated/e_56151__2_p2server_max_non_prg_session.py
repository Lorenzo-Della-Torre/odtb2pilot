"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

testscript: Hilding MEPII
project:    BECM basetech MEPII
author:     GANDER10 (Gustav Andersson)
date:       2020-01-22
version:    1.0
reqprod:    56151

title:
    P2Server_max - non programming session ; 2

purpose:
    P2Server_max is the maximum time for the server
    to start with the response message after the
    reception of a request message.

description:
    The maximum time for P2Server in all sessions except programmingSession is 50ms.

details:
    Implicitly tested by:
        REQPROD 76172 ReadMemoryByAddress (Service 23).
"""
from e_76172_MAIN_1_readmemorybyaddress_s23 import run

if __name__ == '__main__':
    run()
