"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 53929
version: 1
title: Disable monitoring and logging of DTCs
purpose: >
    To prevent logging and monitoring of DTCs when the bootloader executing.

description: >
    ECU shall ensure that monitoring and logging of all diagnostic trouble codes(DTCs) is disabled
    when executing a bootloader(programming session).

details: >
    Verify service-19 is disabled when ECU is in programming session
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_service31 import SupportService31

SE31 = SupportService31()


def verify_active_diag_session(dut, mode, session):
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
    if response.data["details"]["mode"] == mode:
        logging.info("ECU is in %s session as expected", session)
        return True

    logging.error("Test Failed: Expected ECU to be in %s session, received mode %s",
                  session, response.data["details"]["mode"])
    return False


def step_1(dut: Dut):
    """
    action: Verify programming preconditions and set ECU to programming session
    expected_result: ECU should be in programming session after checking programming preconditions
    """
    result = SE31.routinecontrol_requestsid_prog_precond(dut)
    if not result:
        logging.error("Test Failed: Routine control request failed")
        return False

    # Set to programming session
    dut.uds.set_mode(2)

    return verify_active_diag_session(dut, mode=2, session='programming')


def step_2(dut: Dut):
    """
    action: Read ReadDTCInfoSnapshotIdentification while ECU executing bootloader and check ECU is
            in default session after hard reset.
    expected_result: ECU should give negative response '7F' and it should end up in default session
    """
    # Read ReadDTCInfoSnapshotIdentification
    response = dut.uds.dtc_snapshot_ids_1903()

    if response.raw[2:4] != '7F':
        logging.error("Test Failed: Expected negative response for DTC request, received %s",
                      response.raw)
        return False

    logging.info("Received negative response '7F' for DTC request as expected")

    # ECU hard reset
    dut.uds.ecu_reset_1101()

    return verify_active_diag_session(dut, mode=1, session='default')


def run():
    """
    Verify service-19 is disabled when ECU is in programming session
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=40)
        result_step = dut.step(step_1, purpose="Verify programming preconditions and set ECU to "
                                               "programming session")
        if result_step:
            result_step = dut.step(step_2, purpose="Read ReadDTCInfoSnapshotIdentification while "
                                                   "ECU executing bootloader and check ECU is in "
                                                   "default session after hard reset")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
