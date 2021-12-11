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

"""
title: InputOutputControlByIdentifier (2F) - inputOutputControlParameter
       (IOCP) freezeCurrentState (02)
reqprod: 76591
version: 2
purpose:
    Freeze input output state when a fault occurs.
description:
    The ECU may support the service InputOutputControlByIdentifier with data
    parameter inputOutputControlParameter set to freezeCurrentState in all
    sessions where the ECU supports the service InputOutputControlByIdentifier.
details:
    Not used in the finished product.
"""
import logging
import sys

logging.basicConfig(format='%(asctime)s - %(message)s',
                    stream=sys.stdout, level=logging.DEBUG)

logging.info("Testcase result: Not applicable")
