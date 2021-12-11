/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



**********************************************************************************/


"""
title:   Number of logical blocks
reqprod: 397293
version: 1
purpose:
    Define the minimum number of logical block. The actual number of logical
    blocks are defined by the ECU Software Structure.
description:
    The ECU shall contain at least one logical block. The maximum number of
    blocks shall be statically configured in the bootloader.
details:
    Inspect Mentors release notes
"""
import logging
import sys

logging.basicConfig(format='%(asctime)s - %(message)s',
                    stream=sys.stdout, level=logging.DEBUG)

logging.info("Testcase result: To be inspected")
