"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 398371
version: 1
title: Verification Block Table per Software Part
purpose: >
    To enable that each software part is to be signed and verified individually.

description: >
    Each single software part must contain a verification block table, i.e. it will be one
    verification block per logical block defined in the ECU.

details: >
    Implicitly tested script
    Tested implicitly by REQPROD 404693 because VBF file header contains information of
    Verification Block Table such as startAddress & length and Verification Block Table hash.

"""

import logging
import sys
from e_404693_MAIN_3_verification_block_table_header_identifiers import run

logging.basicConfig(format=' %(message)s',stream=sys.stdout, level=logging.INFO)


if __name__ == '__main__':
    run()
