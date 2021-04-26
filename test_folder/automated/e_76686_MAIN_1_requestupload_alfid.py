"""
testscript: Hilding MEPII
project:    BECM basetech MEPII
author:     GANDER10 (Gustav Andersson)
date:       2021-02-09
version:    1.0
reqprod:    76686

title:
    RequestUpload (35) - addressAndLengthFormatIdentifier (ALFID) ; 2

purpose:
    Compliance with VCC tools.

description:
    The ECU shall support RequestDownload - addressAndLengthFormatIdentifier (ALFID)
    with the value 0x44:
        - MemorySize = 4 bytes
        - MemoryAddress = 4 bytes

details:
    Not applicable because it is not requested by Mentor.
"""

import logging
import sys

def run():
    """
    Run - Call other functions from here.
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)
    logging.info("Testcase result: Not applicable")

if __name__ == '__main__':
    run()
