"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.


/*********************************************************************************/

reqprod: 74141
version: 2
title: If a diagnostic service makes a reset, the response shall be sent before making the reset.

purpose: >
    All ECUs need to follow the same sequence since failure to do so may result in different ECUs
    being in different states

description: >
    If a diagnostic service is allowed to make a reset as specified in section Effect on the ECU
    operation, the response shall be sent before performing the reset.

details: >
    Send ECU reset request and verify mode changes to default session from programming/extended
    session and ECU response is 0x51
    Steps-
        1. Perform ECU hard reset from programming session and verify.
        2. Perform ECU hard reset from extended session and verify.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError


def step_1(dut: Dut):
    """
    action: Set ECU to programming session. Verify response and ECU mode changed
            to default from programming session after hard reset.
    expected_result: Positive Response
    """
    dut.uds.set_mode(2)
    ecu_mode = dut.uds.active_diag_session_f186()
    if ecu_mode.data['details']['mode'] == 2:
        # Get response and perform ECU hard reset
        response = dut.uds.ecu_reset_1101()
        ecu_mode = dut.uds.active_diag_session_f186()
        # Extract '51' from response.raw[2:4]
        if response.raw[2:4] == '51' and ecu_mode.data['details']['mode'] == 1:
            return True
        logging.error("Test Failed: Invalid response or ECU hard reset not successful")
        return False
    logging.error("Test Failed: ECU not in programming session before hard reset")
    return False


def step_2(dut: Dut):
    """
    action: Set ECU to extended session. Verify response and ECU mode changed
            to default from extended session after hard reset.
    expected_result: Positive Response
    """
    dut.uds.set_mode(1)
    dut.uds.set_mode(3)
    ecu_mode = dut.uds.active_diag_session_f186()
    if ecu_mode.data['details']['mode'] == 3:
        # Get response and perform ECU hard reset
        response = dut.uds.ecu_reset_1101()
        ecu_mode = dut.uds.active_diag_session_f186()
        # Extract '51' from response.raw[2:4]
        if response.raw[2:4] == '51' and ecu_mode.data['details']['mode'] == 1:
            return True
        logging.error("Test Failed: Invalid response or ECU hard reset not successful")
        return False
    logging.error("Test Failed: ECU not in extended session before hard reset")
    return False


def run():
    """
    Verify ECU response and diagnostic session is changed from programming/extended
    to default session after ECU reset
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=30)
        result_step = dut.step(step_1, purpose="Set ECU to programming session. Verify response "
                               "and ECU mode changed to default from programming session "
                               "after hard reset")
        if result_step:
            result_step = dut.step(step_2, purpose="Set ECU to extended session. Verify response "
                                   "and ECU mode changed to default from extended session "
                                   "after hard reset")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
