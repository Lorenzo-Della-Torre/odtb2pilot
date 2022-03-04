"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.

NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 52281
version: 1
title: No PROG received within Timeout_Prog
purpose: >
    To define next transition when no DiagnosticSessionControl(ProgrammingSession)
    request is received within Timeout_Prog.

description: >
    If no DiagnosticSessionControl(ProgrammingSession) request is received within
    Timeout_Prog shall the ECU enter the Complete & Compatible function.

details: >
    Verify whether the ECU is entering into Complete & Compatible function when
    no DiagnosticSessionControl(ProgrammingSession) request is received within Timeout_Prog
"""

import logging
import time
from hilding.dut import Dut
from hilding.dut import DutTestError


def step_1(dut):
    """
    action: Check whether the ECU is in DefaultSession after hard reset.
    expected_result: ECU is in DefaultSession.
    """
    # ECU hard reset
    dut.uds.generic_ecu_call(bytes.fromhex('1101'))
    # Wait 155 after ECU hard reset (ECU reset time is 150ms)
    time.sleep(0.155)

    # Check active diagnostic session
    response = dut.uds.active_diag_session_f186()
    if response.data["details"]["mode"] == 1:
        return True

    logging.error("Test Failed: Not in DefaultSession, received session %s",
                  response.data["details"]["mode"])
    return False


def run():
    """
    Verify whether the ECU is entering into Complete & Compatible function when
    no DiagnosticSessionControl(ProgrammingSession) request is received within Timeout_Prog
    """

    dut = Dut()

    start_time = dut.start()
    result = False

    try:
        dut.precondition(timeout=60)

        result = dut.step(step_1, purpose="Verify ECU is entering into Complete & Compatible "
                          "when no ProgrammingSession request is received within timeout")

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
