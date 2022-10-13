"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 404620
version: 1
title: Signing Method SHA256_RSA2048 - Public Key Algorithm
purpose: >
    Define the public key algorithm.

description: >
    The public key algorithm shall be: PKCS #1 v2.2: RSA Cryptography Standard, RSA Laboratories,
    October 27, 2012, where the RSASSA-PSS signature scheme shall be used. The signature scheme
    includes a salt when generating a signature. The salt length shall be set to the same length
    as the underlying hash value. This means that the resulting signature will be different every
    time a file is signed.

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
