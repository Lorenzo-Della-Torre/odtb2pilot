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
date:       2021-02-22
version:    1
reqprod:    74140

title:
    P4Server_max for services not supported by the ECU

purpose:
    ECU shall respond swiftly even though service is not supported by the
    ECU since failure to do so may cause problems using functional requests with SPRMB
    bit set.

description:
    The ECU shall use P2Server_max as P4Server_max as timing paramter for negative
    response when receiving requests for diagnostic services not supported by the ECU.

details:
    Implicitly tested by:
        REQPROD 74109 which check all undefined services 0-FF and measures the time
        for each response.
"""

import logging
import sys

def run():
    """
    Run - Call other functions from here.
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    logging.info("Testcase result: Implicitly tested by REQPROD 74109")

if __name__ == '__main__':
    run()
