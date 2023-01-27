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
    If a diagnostic service is allowed to make a reset as specified in section effect on the ECU
    operation, the response shall be sent before performing the reset.

details: >
    Verify positive response for ECU hard reset, also verify that active diagnostic session is
    changed to default from programming/extended session after ECU hard reset
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError


def verify_active_diagnostic_session(dut, mode, session):
    """
    Verify active diagnostic session
    Args:
        dut (Dut): An instance of Dut
        mode (int): Diagnostic session mode
        session (str): Diagnostic session
    Returns:
        (bool): True on successfully verifying active diagnostic session
    """
    response = dut.uds.active_diag_session_f186()
    if response.data['details']['mode'] == mode:
        logging.info("ECU is in %s session as expected", session)
        return True

    logging.error("Test Failed: Expected ECU to be in %s session, but it is in mode %s", session,
                   response.data['details']['mode'])
    return False


def ecu_reset_and_verify_default_session(dut):
    """
    ECU hard reset and verify default session
    Args:
        dut (Dut): An instant of Dut
    Returns:
        (bool): True when ECU is in default session after ECU hard reset
    """
    response = dut.uds.ecu_reset_1101()
    if response.raw[2:4] != '51':
        logging.error("Test Failed: Expected positive response for ECU hard reset, but received %s"
                      , response.raw)
        return False

    return verify_active_diagnostic_session(dut, mode=1, session='default')


def step_1(dut: Dut):
    """
    action: Verify active diagnostic session is changed to default from extended session after ECU
            hard reset
    expected_result: True when ECU is in default session after ECU hard reset
    """
    # Set ECU to extended session
    dut.uds.set_mode(3)

    result = verify_active_diagnostic_session(dut, mode=3, session='extended')
    if not result:
        return False

    return ecu_reset_and_verify_default_session(dut)


def step_2(dut: Dut):
    """
    action: Verify active diagnostic session is changed to default from programming session after
            ECU hard reset
    expected_result: True when ECU is in default session after ECU hard reset
    """
    # Set ECU to programming session
    dut.uds.set_mode(2)

    result = verify_active_diagnostic_session(dut, mode=2, session='programming')
    if not result:
        return False

    return ecu_reset_and_verify_default_session(dut)


def run():
    """
    Verify positive response for ECU hard reset and also verify that active diagnostic session is
    changed to default from programming/extended session after ECU hard reset
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=60)
        result_step = dut.step(step_1, purpose="Verify active diagnostic session is changed to"
                                        " default from extended session after ECU hard reset")
        if result_step:
            result_step = dut.step(step_2, purpose="Verify active diagnostic session is changed to"
                                          " default from programming session after ECU hard reset")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
