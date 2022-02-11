"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.


/*********************************************************************************/

reqprod: 52290
version: 1
title: Reception of the ECUReset service

purpose: >
    To define the behavior when the ECU receives the ECUReset request in the
    programmingSession state.

description: >
    When the ECU receives an ECUReset request, the ECU shall make a reset,
    thus restarting the ECU from Init state.

details: >
    Send ECU reset request and check the ECU restarted from init state for following scenarios-
        1. ECU hard reset
        2. ECU soft reset
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError


def step_1(dut: Dut):
    """
    action: Perform ECU hard reset request and verify ECU is restarted from init state
    expected_result: Positive Response
    """
    dut.uds.set_mode(2)
    ecu_mode = dut.uds.active_diag_session_f186()
    if ecu_mode.data['details']['mode'] == 2:
        response = dut.uds.ecu_reset_1101()
        ecu_mode = dut.uds.active_diag_session_f186()
        # Extract '51' from response.raw[2:4]
        if response.raw[2:4] == '51' and ecu_mode.data['details']['mode'] == 1:
            return True
        logging.error("Test Failed: ECU is not restarted from init state after hard reset")
        return False
    logging.error("Test Failed: ECU not in programming session before hard reset")
    return False

def run():
    """
    Send ECU reset request (soft & hard) and check the ECU restart from init state.
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=30)
        result_step = dut.step(step_1, purpose="ECU hard reset request and verify "
                               "ECU is restarted from init state")

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
