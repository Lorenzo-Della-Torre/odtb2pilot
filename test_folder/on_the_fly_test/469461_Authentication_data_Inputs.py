"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

title: Supporting functional requests
reqprod: 60112
version: 1
purpose:
    Define support for functional requests
description:
    Functional requests shall be supported
details:
    This test is validated using a functional (broadcast) call using the
    address 0x7ff setting the mode on the ECU. Actually, just starting and
    stopping the test would validate the requirement since the heartbeat that
    we wake up the ECU and keeps it awake with, is using functional addressing
    as well. However, writing the test like we have done here makes it more
    explicit.
"""

import logging

from hilding.dut import Dut
from hilding.dut import DutTestError

def step_1(dut: Dut):
    """
    Read did DOC7 and D047
    in mode1 and 2
    """
    dut.uds.read_data_by_id_22(b'\xd0\xc7')
    dut.uds.read_data_by_id_22(b'\xd0\x47')
    dut.uds.set_mode(mode=1)
    dut.uds.set_mode(mode=2)
    dut.uds.read_data_by_id_22(b'\xd0\x47')
    dut.uds.set_mode(mode=1)
    dut.uds.ecu_reset_1101()
    dut.uds.read_data_by_id_22(b'\xd0\x47')


def run():
    """ Supporting functional requests """
    dut = Dut()
    start_time = dut.start()
    result = False
    try:
        dut.precondition()
        dut.step(step_1)
        result = True

    except DutTestError as error:
        logging.error("The testcase for ed_test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)
if __name__ == '__main__':
    run()
