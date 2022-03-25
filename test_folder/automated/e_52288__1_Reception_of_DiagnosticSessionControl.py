"""

/*********************************************************************************/


Copyright © 2022 Volvo Car Corporation. All rights reserved.


NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/


reqprod: 52288
version: 1
title: Reception of DiagnosticSessionControl(defaultSession)

purpose: >
    To define the behaviour when the ECU receives the DiagnosticSessionControl
    (defaultSession) request in the programmingSession state.
description: >
    When the ECU receives a DiagnosticSessionControl(defaultSession) request, the
    ECU shall make a reset, thus restarting the ECU from Init state.

details: >
    ECU status verification after setting to default session from programming Session.
    Verification of default session status of ECU using DiagnosticSessionControl(defaultSession)
    response.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN

SC = SupportCAN()


def step_1(dut: Dut):
    """
    action: Verify ECU status after setting to default session from programming Session
    expected_result: positive response on successful verification of ECU in default session
    """

    dut.uds.set_mode(2)
    response_code = dut.uds.active_diag_session_f186()
    if response_code.data["details"]["mode"] == 2:
        dut.uds.set_mode(1)
        # Check active DiagnosticSession mode
        response_code = dut.uds.active_diag_session_f186()
        if response_code.data["details"]["mode"] == 1:
            return True
    logging.error("Test failed: ECU failed to reset or not in default session, received mode %s",
                  response_code.data["details"]["mode"])
    return False


def run():
    """
    ECU status verification after setting to default session from programming Session.
    """

    dut = Dut()
    start_time = dut.start()
    result = False
    try:
        dut.precondition()
        result = dut.step(
            step_1, purpose="Set ECU to default session from programming Session and"
                            " verify its status")
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
