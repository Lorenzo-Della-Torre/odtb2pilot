"""
title:   CAN frame identifier length
reqprod: 60111
version: 1
purpose:
    Define length of CAN frame identifier
description:
    11-bit CAN frame identifiers shall be used
details:
    Inspection of configuration and inspect dbc-file and check that values are less than 2^12
"""
import logging
import sys

logging.basicConfig(format='%(asctime)s - %(message)s',
                    stream=sys.stdout, level=logging.DEBUG)

logging.info("Testcase result: To be inspected")
