"""

/*********************************************************************************/



Copyright © 2023 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 484030
version: 0
title: ECU physical address
purpose: >
    To dedicate a physical logical address for the ECU

description: >
    Rationale:
    To make it possible for the tester to send a specific request to a public ECU on a
    network in the vehicle, each public ECU needs to have its own unique address. The allocation
    of the address is a part of the internal architectural work at Volvo Cars.
    Req:
    The ECU shall implement one assigned vehicle unique physical logical address. The address
    shall originate from Volvo Car Corporation.

details: >
    Implicitly tested by:
    REQPROD 68177 active diagnostic session data record.
"""

import sys
import logging
from e_68177_MAIN_0_active_diag_session_f186 import run

logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)


if __name__ == '__main__':
    run()
