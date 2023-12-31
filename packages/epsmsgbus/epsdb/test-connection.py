"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

#!/bin/env python

"""
Test database connection.
"""

import argparse
import logging
import sys

import epsdb.core


log = logging.getLogger('test-connection')


def main(argv):
    ap = argparse.ArgumentParser(description="Test database connection.")
    ap.add_argument('-d', '--debug', action="store_true", default=False, help="Print out debug information.")
    args = ap.parse_args(argv)
    if args.debug:
        log.setLevel(logging.DEBUG)
    with epsdb.core.DatabaseContext() as db:
        result, = db.sql("SELECT count(*) FROM testcase_result")
        log.info("OK  - connection '%s' is working." % '|'.join(epsdb.core.CONFIG.connstr))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        main(sys.argv[1:])
    except Exception as e:
        log.error("NOK - trying to connect to '%s'." % '|'.join(epsdb.core.CONFIG.connstr))
        log.error("... No connection to the database %s." % str(e))
        log.debug("TRACE", exc_info=True)

# eof
