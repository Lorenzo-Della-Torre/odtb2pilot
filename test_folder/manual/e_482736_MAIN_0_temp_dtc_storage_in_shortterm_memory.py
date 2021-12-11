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

""" Testscript for a requirement which needs to be tested by code inspection (To be inspected)

    Testscript  Hilding MEPII
    project     BECM basetech MEPII
    author      J-ASSAR1 (Joel Assarsson)
    date        2020-11-26
    version     1.0

    ID:         482736
    Title:      Temporary DTC Storage in short-term memory
    Purpose:    To ensure storage capacity in short-term memory.
    Descr.:     ECUs that temporarily stores DTC information in the short-term memory before
                transferring it to long-term memory shall have the same amount of data storage
                capability in both memory types.
"""

import logging
import sys

logging.basicConfig(format='%(asctime)s - %(message)s',
                    stream=sys.stdout, level=logging.DEBUG)

logging.info("Testcase result: To be inspected")
