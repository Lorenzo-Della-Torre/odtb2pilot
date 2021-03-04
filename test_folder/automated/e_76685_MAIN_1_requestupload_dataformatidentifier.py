"""
testscript: ODTB2 MEPII
project:    BECM basetech MEPII
author:     GANDER10 (Gustav Andersson)
date:       2021-02-09
version:    1.0
reqprod:    76685

title:
    RequestUpload (35) - dataFormatIdentifier (DFI_) ; 2

purpose:
    Compliance with VCC tools.

description:
    The ECU shall encode the dataFormatIdentifier (DFI_) with the value 0x00.

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
