"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.


NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/


reqprod: 52285
version: 1
title: Receive and process diagnostic programming session requests

purpose: >
    To define when the ECU shall be able to receive and process a diagnostic programming
    session request.

description: >
    When the ECU is in programmingSession state, it shall be able to receive and process
    diagnostic programming session requests.

details: >
    verify if ECU shall be able to receive and process diagnostic programming session
    requests when it is in programmingSession state.
    Steps-
    1. Set to programming session
    2. Set to programming session again based on valid response of 0x50
    3. verify ECU is able to process diagnostic programming session request based on
       valid response (0x50)
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN

SC = SupportCAN()


def step_1(dut: Dut):
    """
    action: Verify ECU is able to receive and process diagnostic programming session requests
    in programmingSession state
    expected_result: positive response
    """
    # set to programming session twice based on valid response of 0x50
    for _ in range(2):
        dut.uds.set_mode(2)
        response = SC.can_messages[dut["receive"]][0][2][2:4]
        # Check active DiagnosticSession mode
        response_code = dut.uds.active_diag_session_f186()
        if response_code.data["details"]["mode"] == 2 and response == '50':
            result = True
        else:
            result = False
            break
    if result:
        return True
    logging.error("Test failed: Invalid response and ECU not processed diagnostic programming "
                  "session request")
    return False


def run():
    """
    Verify ECU is able to receive and process diagnostic programming session requests when it is
    in programmingSession state, based on valid response (0x50)
    """

    dut = Dut()
    start_time = dut.start()
    result = False
    try:
        dut.precondition()
        result = dut.step(step_1, purpose="Set to programming session and verify ECU process"
                          " diagnostic programming session request")
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
