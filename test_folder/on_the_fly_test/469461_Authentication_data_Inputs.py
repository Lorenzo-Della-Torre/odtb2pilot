"""
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
