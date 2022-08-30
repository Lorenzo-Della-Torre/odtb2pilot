"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 410732
version: 0
title: Default Signing Method
purpose: >
    Define the default signing method. The ECU shall use the default signing method, unless else
    is explicitly defined elsewhere, e.g. in the LC : Diagnostics and ECU Platform.

description: >
    The default signing method shall be SHA256_RSA2048_sw_part_based.

details: >
    Implicitly tested script
    Tested implicitly by req-400425 because req covers software download.
"""

import logging
import sys
from e_400425_MAIN_2_programming_of_logical_blocks import run

logging.basicConfig(format=' %(message)s',stream=sys.stdout, level=logging.INFO)

if __name__ == '__main__':
    run()
