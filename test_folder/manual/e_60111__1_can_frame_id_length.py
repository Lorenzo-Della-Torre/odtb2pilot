"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

"""
title:   CAN frame identifier length
reqprod: 60111
version: 1
purpose:
    Define length of CAN frame identifier
description:
    11-bit CAN frame identifiers shall be used
details:
    Inspection of configuration and inspect dbc-file and check that values are less than 2^12
"""
import logging
import sys

logging.basicConfig(format='%(asctime)s - %(message)s',
                    stream=sys.stdout, level=logging.DEBUG)

logging.info("Testcase result: To be inspected")
