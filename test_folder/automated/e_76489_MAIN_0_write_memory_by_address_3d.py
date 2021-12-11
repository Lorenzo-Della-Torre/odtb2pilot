"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

"""
testscript: Hilding MEPII
project:    BECM basetech MEPII
author:     GANDER10 (Gustav Andersson)
date:       2021-02-10
version:    1
reqprod:    76489

title:
    WriteMemoryByAddress (3D)

purpose:
    The service WriteMemoryByAddress may be useful during the development process.

description:
    The ECU shall support the service WriteDataByAddress if the ECU is involved
    in propulsion or safety functions in the vehicle. Otherwise, the ECU may
    supportthe service WriteDataByAddress. If implemented, the ECU shall
    implement the service accordingly:

    Supported sessions:
        The ECU shall support Service WriteDataByAddress in:
            - defaultSession
            - extendedDiagnosticSession
        The ECU shall not support service WriteDataByAddress in programmingSession.

    Response time:
        Maximum response time for the service writeMemoryByAddress (0x3D) is 5000ms.

    Effect on the ECU normal operation:
        The service writeMemoryByAddress (0x3D) is allowed to affect the ECU’s
        ability to execute non-diagnostic tasks. The service is only allowed to
        affect execution of the non-diagnostic tasks during the execution of the
        diagnostic service. After the diagnostic service is completed any effect
        on the non-diagnostic tasks is not allowed anymore
        (normal operational functionality resumes). The service shall not reset the ECU.

    Entry conditions:
        Entry conditions for service writeMemoryByAddress (0x3D) are allowed only if
        approved by Volvo Car Corporation. If the ECU implement safety requirements
        with an ASIL higher than QM it shall, in all situations when diagnostic services
        may violate any of those safety requirements, reject the critical diagnostic
        service requests. Note that if the ECU rejects such critical diagnostic service
        requests, this requires an approval by Volvo Car Corporation.

    Security access:
        The ECU may protect service writeMemoryByAddress by using the service
        securityAccess (0x27). If the memory part includes data protected by security
        access for write access using service writeDataByIdentifier (0x2E), then the
        service shall be protected by security access when including this same data
        (completely or partly) in the dynamically defined dataIdentifier.


details:
    Not applicable. This service is not used by Volvo Car Corporation as of writing this
    script.
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
