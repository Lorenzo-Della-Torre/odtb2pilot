"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 404623
version: 0
title: Signing Method SHA256_RSA2048 - Key Size
purpose: >
    Define the key size for the private- and public key.

description: >
    The key size shall be 2048 bits. This is the size of the modulus part of the key
    representations.

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
