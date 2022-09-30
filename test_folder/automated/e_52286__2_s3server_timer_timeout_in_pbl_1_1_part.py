"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/


reqprod: 52286
version: 2
title: S3Server timer timeout in PBL

purpose: >
    To define the behaviour when S3server times out in PBL.

description: >
    If S3server times out when running PBL, the ECU shall make a test on Complete and Compatible
    function and if Complete and Compatible function returns PASSED the ECU shall make a reset.

details: >
    Verify behaviour of ECU's S3server times out in PBL session.
"""

import time
import logging
from hilding.dut import DutTestError
from hilding.dut import Dut
from supportfunctions.support_service31 import SupportService31
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service3e import SupportService3e

SE22 = SupportService22()
SE31 = SupportService31()
SE3E = SupportService3e()


def verify_active_diagnostic_session(dut, mode, session):
    """
    Request to check active diagnostic session
    Args:
        dut (Dut): An instance of Dut
        mode (int): ECU mode
        session (str): Diagnostic session
    Returns:
        (bool): True on successfully verified active diagnostic session
    """
    active_session = SE22.read_did_f186(dut, mode)
    if active_session:
        logging.info("ECU is in %s session as expected", session)
        return True

    logging.error("Test Failed: ECU is not in %s session", session)
    return False


def step_1(dut: Dut):
    """
    action: Verify programming preconditions
    expected_result: Programming preconditions should be verified
    """
    SE3E.stop_periodic_tp_zero_suppress_prmib()
    result = SE31.routinecontrol_requestsid_prog_precond(dut)
    if result:
        logging.info("Successfully verified programming preconditions")
        return True

    logging.error("Test Failed: Unable to verify routine control request sid prog preconditions")
    return False


def step_2(dut: Dut):
    """
    action: Set ECU in programming session and verify active diagnostic session
    expected_result: ECU should be in programming session
    """
    # Set to programming session
    dut.uds.set_mode(2)

    # Verify active diagnostic session
    return verify_active_diagnostic_session(dut, mode=b'\x02', session='programming')


def step_3(dut: Dut):
    """
    action: Wait shorter than timeout and verify ECU is in programming session
    expected_result: True when ECU is in programming session
    """
    # Wait shorter than timeout for staying in current mode
    logging.info("Waiting 4 seconds to send a diagnostic request just before S3 Server times out")
    time.sleep(4)

    # Verify active diagnostic session
    return verify_active_diagnostic_session(dut, mode=b'\x02', session='programming')


def step_4(dut: Dut):
    """
    action: Wait longer than timeout and verify ECU is in default session
    expected_result: True when ECU is in default session
    """
    # Wait longer than timeout for staying in current mode
    logging.info("Waiting 6 seconds to send a diagnostic request just after S3 Server times out")
    time.sleep(6)

    # Verify active diagnostic session
    return verify_active_diagnostic_session(dut, mode=b'\x01', session='default')


def run():
    """
    Verify behaviour of ECU's S3server times out in PBL session
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=60)

        result_step = dut.step(step_1, purpose="Verify programming preconditions")
        if result_step:
            result_step = dut.step(step_2, purpose="Set ECU in programming session and verify"
                                                   " active diagnostic session")
        if result_step:
            result_step = dut.step(step_3, purpose="Wait shorter than timeout and verify"
                                                   " ECU is in programming session")
        if result_step:
            result_step = dut.step(step_4, purpose="Wait longer than timeout and verify"
                                                   " ECU is in default session")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
