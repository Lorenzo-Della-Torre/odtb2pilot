"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 466659
version: 0
title: Data Compression Method 2
purpose: >
    State the compression method #2

description: >
    The data compression/decompression method #2 shall be LZMA.
    Note: Data_format_identifier for compression method #2 is specified in
    [VCC-UDS Services, REQPROD 459337]. LZMA SDK (version 18.01) and specification can be
    downloaded from http://www.7-zip.org/sdk.html

details: >
    Implicitly tested script
    Tested implicitly by REQPROD 400425 because compression is done by VECS and if the
    decompression did not work in the ECU, SWDL would fail.
"""

import logging
import sys
from e_400425_MAIN_2_programming_of_logical_blocks import run

logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

if __name__ == '__main__':
    run()
