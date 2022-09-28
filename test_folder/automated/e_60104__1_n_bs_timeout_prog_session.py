"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 60104
version: 1
title: N_Bs timeout in programming session
purpose: >
    From a system perspective it is important that both sender and receiver side times out roughly
    the same time. The timeout value shall be high enough to not be affected by situations like
    occasional high busloads and low enough to get a user friendly system if for example an ECU
    is not connected.

description: >
    N_Bs timeout value shall be 1000ms in programming session.

details: >
    Implicitly tested script
    Tested implicitly by REQPROD 60102 because N_Bs and N_As(Network layer timing parameter)
    timeout value is 1000ms in programming session
"""

import logging
import sys
from e_60102__1_n_as_timeout_prog_session import run

logging.basicConfig(format=' %(message)s',stream=sys.stdout, level=logging.INFO)


if __name__ == '__main__':
    run()
