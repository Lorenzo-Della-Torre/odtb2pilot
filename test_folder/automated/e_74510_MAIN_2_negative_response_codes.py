"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 74510
version: 2
title: Negative response code other than generalReject (0x10) and  busyRepeatRequest (0x21).

purpose: >
    Standardize the negative response codes that an ECU may send to make it easier to understand
    why a ECU rejects a diagnostic service request.

description: >
    Rationale:
        The ECU will implement negative response codes that are specified
        in ISO 14229-1 according to their definition and NRC handling sequence.

    Req:
        Negative response code (other than generalReject (0x10) and
        busyRepeatRequest (0x21)) sent by negative responses on diagnostic
        services requests is allowed as specified by ISO 14229-1 unless
        otherwise is specified by this document.

details: >
    Implicitly tested script
    Tested implicitly by REQPROD 76172 which verifies a negative response in programming session.
"""

import logging
import sys
from e_76172_MAIN_0_readmemorybyaddress_s23 import run

logging.basicConfig(format=' %(message)s',stream=sys.stdout, level=logging.INFO)


if __name__ == '__main__':
    run()
