"""
title:   Number of logical blocks
reqprod: 397293
version: 1
purpose:
    Define the minimum number of logical block. The actual number of logical
    blocks are defined by the ECU Software Structure.
description:
    The ECU shall contain at least one logical block. The maximum number of
    blocks shall be statically configured in the bootloader.
details:
    Inspect Mentors release notes
"""
import logging
import sys

logging.basicConfig(format='%(asctime)s - %(message)s',
                    stream=sys.stdout, level=logging.DEBUG)

logging.info("Testcase result: To be inspected")
