"""
testscript: ODTB2 MEPII
project:    BECM basetech MEPII
author:     GANDER10 (Gustav Andersson)
date:       2021-02-08
version:    1.0
reqprod:    74510

title:
    Negative response code other than generalReject (0x10)
    and busyRepeatRequest (0x21) ; 3

purpose:
    Standardise the negative response codes that an ECU may
    send to make it easier to understand why a ECU rejects a
    diagnostic service request.

description:
    Rationale:
        The ECU will implement negative response codes that are specified
        in ISO 14229-1 according to their definition and NRC handling sequence.

    Req:
        Negative response code (other than generalReject (0x10) and
        busyRepeatRequest (0x21)) sent by negative responses on diagnostic
        services requests is allowed as specified by ISO 14229-1 unless
        otherwise is specified by this document.


details:
    Implicitly tested by:
        REQPROD 76172 which verifies a negative response in programming session.
        There are also serveral other REQPRODs which test this.
        E.g. REQPROD 76173
"""

import logging
import sys

def run():
    """
    Run - Call other functions from here.
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    logging.info("Testcase result: Implicitly tested by REQPROD 76172")

if __name__ == '__main__':
    run()
