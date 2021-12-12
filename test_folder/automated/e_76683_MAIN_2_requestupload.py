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
date:       2021-02-09
version:    1.0
reqprod:    76683

title:
    RequestUpload (35) ; 3

purpose:
    Compliance with VCC tools.

description:
    The ECU may support the service RequestUpload (0x35). If supported,
    the ECU shall implement the service accordingly:

    Supported sessions:
        The ECU shall support service RequestUpload in
        programmingSession, both primary and secondary bootloader.

        The ECU shall not support service RequestUpload in:
            - defaultSession
            - extendedDiagnosticSession

    Response time:
        Maximum response time for the service RequestUpload (0x35) is 1000ms.

    Entry conditions:
        The ECU shall not implement entry conditions for service
        Request RequestUpload Download (0x35).

    Security access:
        The ECU shall protect service RequestUpload (0x35) by
        using the service securityAccess (0x27).

details:
    Not applicable because it is not requested by Mentor.
"""

import logging
import sys

def run():
    """
    Run - Call other functions from here.
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)
    logging.info("Testcase result: Not applicable")

if __name__ == '__main__':
    run()
