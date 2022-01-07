"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76697
version: 5
title: RequestTransferExit (37) - transferResponseParameterRecord - algorithm.
purpose: >
    Compliance with VCC tools. Define the checksum algorithm.

description: >
    If the transfer of data is initiated by RequestDownload or RequestUpload and a checksum
    is required, then the transferResponseParameterRecord checksum calculation shall use the
    CRC16-CCITT algorithm (initial value 0xFFFF and normal representation). The checksum shall
    be calculated on all data bytes as defined by the diagnostic services RequestDownload or
    RequestUpload. Hint. For algorithm compliance checking: use the example described in
    section Appendix A- Suggestion code for transferResponseParameterRecord calculation.

details: >
    As per REQ 404693 we are using only Alternative 1 and this matches with Vbf version 2.6.
    In PageNo 27, the flowchart for Vbf 2.6 Version supports check memory, so no CRC will
    be available in (transferResponseParameterRecord). So CRC Calculation will not applicable.
    In this case REQ 76697 is NA.
"""

import logging
import sys

logging.basicConfig(format=' %(message)s',
                    stream=sys.stdout, level=logging.INFO)

logging.info("Testcase result: Not applicable")
