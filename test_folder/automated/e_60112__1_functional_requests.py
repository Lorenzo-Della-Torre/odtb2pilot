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
import sys

from hilding.dut import Dut
from hilding.dut import DutTestError

def step_1(dut: Dut):
    """
    action:
        Change ECU mode using functional addresssing
    expected_result: >
        ECU: positive result
    """
    # the .dbc files have the following information
    # spa1:
    #  BO_ 2047 Vcu1ToAllFuncFront1DiagReqFrame: 8 VCU1
    #   SG_ Vcu1ToAllFuncFront1DiagReqNpdu : 7|64@0+ (1,0) [0|0]
    #   "" BECM, ECM, ESM, IGM, ISGM, MVCM, TCM
    # spa2:
    #  BO_ 2047 HvbmdpToAllUdsDiagRequestFrame : 8 HVBMdp
    #   SG_ HvbmdpToAllUdsHvbm1canNPdu : 7|64@0+ (1,0) [0|0]
    #   "" HVBM
    # note: 2047 decimal = 0x7ff
    # hence, we set the addressing as follows:
    parameters = dut.get_platform_yml_parameters(__file__)
    dut.send = parameters.get("send")
    logging.info("dut.send = %s", dut.send)
    if not dut.send:
        raise DutTestError("Your platform is not supported in this test")

    dut.uds.set_mode(2)

    if dut.uds.mode != 2:
        raise DutTestError("Could not change mode using functional addressing")

    # reset the send signal to original setting
    dut.send = dut.conf.rig.signal_send

def run():
    """ Supporting functional requests """

    logging.basicConfig(
        format=" %(message)s", stream=sys.stdout, level=logging.DEBUG)

    dut = Dut()
    start_time = dut.start()

    result = False
    try:
        dut.precondition()
        dut.step(step_1)

        result = True
    except DutTestError as error:
        logging.error("The testcase for 60112 failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
