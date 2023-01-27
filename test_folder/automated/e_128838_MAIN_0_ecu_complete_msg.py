"""

/*********************************************************************************/



Copyright © 2023 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 128838
version: 1
title: ECU ability to receive a complete message
purpose: >
    To ensure performance and predictable response times. This requirement does not apply to
    request and response messages gatewayed through a gateway.

description: >
    The ECU shall be able to receive a complete request message (receiving a queued request
    excluded) without to halt the message, while sending of it is in progress, with the help of
    services in lower OSI-layer e.g network/transport layer

details: >
    Implicitly tested script
    Tested implicitly by REQPROD 60017
"""

import logging
import sys
from e_60017__1_n_as_timeout_non_prog_session import run

logging.basicConfig(format=' %(message)s',stream=sys.stdout, level=logging.INFO)


if __name__ == '__main__':
    run()
