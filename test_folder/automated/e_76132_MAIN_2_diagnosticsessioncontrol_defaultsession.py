"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
reqprod: 76132
version: 2
title: DiagnosticSessionControl (10) - defaultSession (01, 81)
purpose: >
    The ECU shall support a method in which the tester can make the ECU revert back to default
    session.

description: >
    The ECU shall support the service diagnosticSessionControl - defaultSession in
    1.	defaultSession
    2.	extendedDiagnosticSession
    3.	programmingSession, both primary and secondary bootloader

details:
    Verify the ECU shall be in default session after reset
"""
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_file_io import SupportFileIO

SE22 = SupportService22()
SIO = SupportFileIO


def verify_active_session(dut: Dut):
    """
    Verify the active diagnostic session
    Args:
        dut(class object): dut instance
    Returns:
        (bool): True when ECU is in default session
    """
    # Read active diagnostic session
    active_session = SE22.read_did_f186(dut, b'\x01')
    if not active_session:
        logging.error(" ECU not in default session")
        return False

    logging.info("ECU is in default session")
    return True

def step_1(dut: Dut):
    """
    action: Verify ECU is in default session
    expected_result:True on receiving positive response and session equal to default
    """
   # Set to default session
    dut.uds.set_mode(1)

   # Read active diagnostic session
    session_without_reset = verify_active_session(dut)
    return session_without_reset

def step_2(dut: Dut):
    """
    action: Verify ECU is in default session after reset
    expected_result: True on receiving positive response and session equal to default
    """
   # Set to extended session
    dut.uds.set_mode(3)

   # ECU hard reset without reply
    dut.uds.ecu_reset_noreply_1181()

   # Read active diagnostic session after reset request
    session_after_reset = verify_active_session(dut)
    return session_after_reset

def step_3(dut: Dut):
    """
    action: Verify ECU is in default session after reset
    expected_result: True on receiving positive response and session equal to default
    """
   # Set to programming session
    dut.uds.set_mode(2)

    # ECU hard reset without reply
    dut.uds.ecu_reset_noreply_1181()

  # Read active diagnostic session after reset request
    session_after_reset = verify_active_session(dut)
    return session_after_reset

def run():
    """
    Verify ECU shall be in default session after reset in all supported sessions
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=30)

        result_step = dut.step(step_1, purpose="Set mode to default and verify "
                             " that ECU is in default session")
        if result_step:
            result_step = dut.step(step_2, purpose="Set mode to extended and verify "
                             " that ECU reverts back to default session after reset")

        if result_step:
            result_step = dut.step(step_3, purpose="Set mode to programming and verify "
                             " that ECU reverts back to default session after reset")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
