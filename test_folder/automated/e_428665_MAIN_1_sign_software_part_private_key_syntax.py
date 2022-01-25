"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 428665
version: 1
title: Sign Software Part - Private Key syntax
purpose: >
    Define the key representation for key distribution at
    test & development and for development tool usage.

description: >
    The Private key shall be represented in an unencrypted PKCS #8 PrivateKeyInfo format
    as defined in PKCS #8: Private-Key Information Syntax Standard, RSA Laboratories
    Technical Note Version 1.2, Revised November 1, 1993.

    The PrivateKey part of of the PrivateKeyInfo shall be a represented as an ASN.1 type
    RSAPrivateKey as defined in PKCS #1 v2.2: RSA Cryptography Standard, RSA Laboratories,
    October 27, 2012.

    The Private Key shall be stored using the PEM format (base64 encoded data)
    as defined in RFC1421.

details: >
    Implicitly tested script
    Tested implicitly by REQPROD 76696 because the SWDL works with public key to decrypt
    the vbf file, expected the same behavior with private production key.
"""

import logging
import sys

logging.basicConfig(format=' %(message)s',
                    stream=sys.stdout, level=logging.INFO)

try:
    from e_76696_MAIN_5_request_transfer_exit_transfer_response_parameter_record import run
except ModuleNotFoundError as err:
    logging.error(
        "The test that is used to test this requirement can't be found: %s found", err)

if __name__ == '__main__':
    run()
