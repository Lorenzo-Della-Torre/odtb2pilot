"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 53975
version: 1
title: Separate memory sectors
purpose: >
    To decrease the total programming time it shall be possible to replace only the specific data
    file that shall be replaced and not being forced to replace all software(s) that already is
    present in the ECU.

description: >
    Two or more data files shall not share a memory sector.

details: >
    Implicitly tested script
    Tested implicitly by REQPROD 397292 because software part number is tested with software
    download principle.
"""

import logging
import sys
from e_397292_MAIN_2_software_parts_per_logical_block import run

logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

if __name__ == '__main__':
    run()
