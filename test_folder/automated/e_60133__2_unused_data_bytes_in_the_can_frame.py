"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 60133
version: 2
title: Unused data bytes in the CAN frame
purpose: >
    Define what to do with data not used in the USDT frame.

description: >
    Unused data byte shall be padded with 0x00 and the receiver of the frame shall ignore padding.

details: >
    Implicitly tested script
    Tested implicitly by REQPROD 60129
"""

import logging
import sys

from e_60129__3_length_of_classic_can_frames import run

logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

if __name__ == '__main__':
    run()
