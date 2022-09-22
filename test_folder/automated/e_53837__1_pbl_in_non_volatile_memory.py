"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 53837
version: 1
title: PBL in non-volatile memory
purpose: >
    The PBL shall always be present in an ECU.

description: >
    The primary bootloader shall be pre-programmed in the non-volatile memory by the ECU
    manufacturer.

details: >
    Implicitly tested script
    Tested implicitly by REQPROD 53839 because it verifies that PBL memory is protected from
    unintentional erasure.
"""

import logging
import sys
from e_53839__2_protected_boot_sector import run

logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

if __name__ == '__main__':
    run()
