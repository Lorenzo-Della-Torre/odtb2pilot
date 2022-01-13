"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76698
version: 6
title: RequestTransferExit (37) - transferResponseParameterRecord - use non-volatile memory.
purpose: >
    Compliance with VCC tools.

description: >
    The checksum (transferResponseParameterRecord) shall always be calculated on data read
    from the actual non-volatile memory as defined by the RequestDownload or RequestUpload.

details: >
    As per REQ 404693 we are using only Alternative 1 and this matches with Vbf version 2.6.
    In PageNo 27, the flowchart for Vbf 2.6 Version supports check memory, so no CRC will
    be available in (transferResponseParameterRecord). So CRC Calculation will not applicable.
    In this case REQ 76698 is NA.
"""

import logging
import sys

logging.basicConfig(format=' %(message)s',
                    stream=sys.stdout, level=logging.INFO)

logging.info("Testcase result: Not applicable")
