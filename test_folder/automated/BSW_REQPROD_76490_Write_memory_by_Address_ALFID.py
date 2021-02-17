"""
testscript: ODTB2 MEPII
project:    BECM basetech MEPII
author:     GANDER10 (Gustav Andersson)
date:       2021-02-10
version:    1
reqprod:    76490

title:
    WriteMemoryByAddress (3D) - addressAndLengthFormatIdentifer (ALFID)

purpose:
    Compliance with VOLVO CAR CORPORATION tools.

description:
    The ECU shall support the service writeMemoryByAddress with the data parameter
    addressAndLengthFormatIdentifier (ALFID) set to one of the following values:

        - 0x14
        - 0x24

    The ECU shall support the data parameter in all sessions where the ECU supports
    the service dynamicallyDefineDataIdentifier - defineByMemoryAddress.

details:
    Not applicable. This service is not used by Volvo Car Corporation as of writing this
    script.
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
