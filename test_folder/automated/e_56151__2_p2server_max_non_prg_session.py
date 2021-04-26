"""
testscript: Hilding MEPII
project:    BECM basetech MEPII
author:     GANDER10 (Gustav Andersson)
date:       2020-01-22
version:    1.0
reqprod:    56151

title:
    P2Server_max - non programming session ; 2

purpose:
    P2Server_max is the maximum time for the server
    to start with the response message after the
    reception of a request message.

description:
    The maximum time for P2Server in all sessions except programmingSession is 50ms.

details:
    Implicitly tested by:
        REQPROD 76172 ReadMemoryByAddress (Service 23).
"""

import logging
import sys

def run():
    """
    Run - Call other functions from here.
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    logging.info("Testcase result: Implicitly tested by "\
    "REQPROD 76172 (ReadMemoryByAddress)")

if __name__ == '__main__':
    run()
