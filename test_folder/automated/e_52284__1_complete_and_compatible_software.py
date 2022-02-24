"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 52284
version: 1
title: Complete and compatible software(s)
purpose: >
    To define the action when the software(s) is/are complete and compatible.

description: >
    If the return value from the Complete & Compatible function is equal to PASSED, it is
    safe to start the application.

details: >
    Verifying ECU boots up the application once the SW is verified as
    complete and compatible
"""


import logging
from hilding.dut import Dut
from hilding.dut import DutTestError


def step_1(dut: Dut):
    """
    action: Verifying ECU boots up the application once the SW is verified as
            complete and compatible

    expected_result: Positive response
    """
    # ECU hard reset
    dut.uds.ecu_reset_1101()

    # Read active diagnostic session
    active_session = dut.uds.active_diag_session_f186()

    # confirming active session
    if active_session.data["details"]["mode"] == 1:
        logging.info("ECU is in Default session")
        return True

    logging.error("Test Failed: ECU Not in Default session")
    return False


def run():
    """
    Verifying ECU boots up the application once the SW is verified as complete and compatible
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=60)
        result_step = dut.step(step_1, purpose='ECU boots up the application once the SW is'
                              ' verified as complete and compatible')
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
