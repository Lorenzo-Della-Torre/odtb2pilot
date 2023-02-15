"""

/*********************************************************************************/



Copyright © 2023 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 113482
version: 3
title: Session Layer
purpose: >
    Standardise communication to ensure all ECUs uses the same diagnostic communication
    specifications. ISO standard shall be followed to reduce cost and make implementation easier

description: >
    The session layer defined in Road vehicles — Unified diagnostic services — Part 2: Session
    layer services Edition 1: 2013 shall be implemented with restriction/additions defined by the
    following VCC requirements.

details: >
    Implicitly tested script
    Tested implicitly by all diagnostic tests, e.g. by REQPROD 76170
"""
import logging
import sys
from e_76170_MAIN_1_service_22_dids import run

logging.basicConfig(format=' %(message)s',stream=sys.stdout, level=logging.INFO)


if __name__ == '__main__':
    run()
