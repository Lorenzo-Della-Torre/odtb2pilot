"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 128777
version: 0
title: ISO specified routines.
purpose: >
    Routines defined by ISO that shall or may be supported

description: >
    Routines with routine identifiers in the range as specified in the table below shall be
    implemented as they are defined by ISO 14229-1.

    (Description) ISO specified routines -> (Identifier range) FF02 – FFFF

    It shall be possible to control the control routine by using the diagnostic service
    specified in Ref[LC : VCC - UDS Services - Service 0x31 (RoutineControl) Reqs].

details: >
    Not applicable because we have no DIDs in that range

"""

import logging
import sys

logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

logging.info("Testcase result: Not applicable")
