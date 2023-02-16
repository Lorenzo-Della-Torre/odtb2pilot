"""

/*********************************************************************************/



Copyright © 2023 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 392111
version: 1
title: bootloader CAN busoff handling
purpose: >
    To increase availablility of the system. Avoid that an ECU gets stuck in bus-off state, or
    exits programming session due to network errors.

description: >
    If hardware support automatic CAN busoff recovery, that recovery mechanism shall be enabled.
    If hardware doesn't support automatic bus-off recovery the bootloader shall check all active
    CAN controllers for bus-off status at maximum 10 ms intervals and if bus-off is detected start
    the bus-off recovery sequence within 10ms.
    This requirement applies to Primary Boot Loader (PBL) and Secondary Boot Loader (SBL).
    Note: If a permanent busoff condition is detected that can not be recovered, and a complete
    and compatible application exist, the S3server timer shall still run and will finally elapse,
    causing and exit of the programming session.


details: >
    Verify automatic CAN busoff recovery in bootloader.
    When in primary bootloader (PBL):
    - short busoff is applied. ECU shall recover and stay in PBL.
    - long busoff is applied. ECU shall recover and switch to default session.
    When in secondary bootloader (SBL):
    - short busoff is applied. ECU shall recover and stay in SBL.
    - long busoff is applied. ECU shall recover and switch to default session.

"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError

from supportfunctions.support_sec_acc import SecAccessParam
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_SBL import SupportSBL

SE22 = SupportService22()
SSBL = SupportSBL()

def long_busoff(dut: Dut):
    """
    Verify ECU recovers and is in default session after a long can busoff
    (more than 5sec)
    Args:
        dut (Dut): An instance of Dut
    Returns:
        true if ECU recovers and is in default session
    """

    # wait for operator to physicaly do a more than 5sec busoff
    input("Do more than 5sec busoff then press enter ")

    # let ECU recover
    logging.info("ECU is recovering")
    time.sleep(5)

    # verify ECU is in default session
    active_session = dut.uds.active_diag_session_f186()
    active_session = active_session.data["details"]["mode"]
    if active_session != 1:
        logging.error("ECU is not in default session. Current session is %s", active_session)
        return False
    logging.info("ECU is in default session as expected")

    return True

def short_busoff(dut: Dut, expected_mode):
    """
    Verify ECU recovers and is in programming session PBL after a short can busoff
    (less than 5sec)
    Args:
        dut (Dut): An instance of Dut
    Returns:
        true if ECU recovers and is in programming session
    """

    # wait for operator to physicaly do a less than 5sec busoff
    input("Do less than 5sec busoff (2sec recommended) then press enter ")

    # let ECU recover
    logging.info("ECU is recovering")
    time.sleep(5)

    # verify ECU is in correct session
    active_session = dut.uds.active_diag_session_f186()
    active_session = active_session.data["details"]["mode"]
    if active_session != 2:
        logging.error("ECU is not in programming session. current session is %s",active_session)
        return False
    logging.info("ECU is in programming session as expected")

    # verify ECU stays in the correct mode
    current_mode = "none"
    if SE22.verify_pbl_session(dut):
        current_mode = "PBL"
    if SE22.verify_sbl_session(dut):
        current_mode = "SBL"

    if expected_mode == current_mode:
        logging.info("ECU is in %s as expected",current_mode)
        return True
    logging.error("ECU is in %s. Expected %s",current_mode,expected_mode)
    return False


def step_1(dut: Dut):
    """
    Action: Switch to programming session PBL and verify
    Expected result: ECU is in programming session PBL
    """
    # switch to programming session
    dut.uds.set_mode(2)

    # verify ECU is in programming session PBL
    if SE22.verify_pbl_session(dut):
        logging.info("ECU is in programming session PBL as expected")
        return True

    logging.error("ECU is not in programming session PBL")
    return False

def step_2(dut: Dut):
    """
    Action: Verify ECU recovers and is in programming session PBL after a short can busoff
    (less than 5sec)
    Expected result: ECU recovers and is in programming session
    """

    return short_busoff(dut,expected_mode="PBL")

def step_3(dut: Dut):
    """
    Action: Verify ECU recovers and is in default session after a long can busoff
    (more than 5sec)
    Expected result: ECU recovers and is in default session
    """

    return long_busoff(dut)

def step_4(dut: Dut):
    """
    Action: Download and activate SBL
    Expected result: ECU is in programming session SBL
    """

    # Set ECU to programming session
    dut.uds.set_mode(2)
    time.sleep(5)

    # Setting up keys
    sa_keys: SecAccessParam = dut.conf.default_rig_config

    # Load VBF files
    result = SSBL.get_vbf_files()
    if not result:
        logging.error("Test Failed: Unable to load VBF files")
        return False

    # SBL activation
    result_ssbl_active = SSBL.sbl_activation(dut, sa_keys)
    if not result_ssbl_active:
        logging.error("Test Failed: Unable to activate SBL")
        return False

    # Get current ECU mode
    ecu_mode = SE22.verify_sbl_session(dut)
    if not ecu_mode:
        logging.error("Test Failed: Expected ECU to be in SBL session")
        return False

    logging.info("ECU is in programming session SBL")

    return True

def step_5(dut: Dut):
    """
    Action: Verify ECU recovers and is in programming session SBL after a short can busoff
    (less than 5sec)
    Expected result: ECU recovers and is in programming session
    """

    return short_busoff(dut,expected_mode="SBL")

def step_6(dut: Dut):
    """
    Action: Verify ECU recovers and is in default session after a long can busoff
    (more than 5sec)
    Expected result: ECU recovers and is in default session
    """

    return long_busoff(dut)

def run():
    """
    Verify ECU behavior when a busoff occurs in bootloader.
    For a short busoff (less than 5sec), ECU shall recover and stay in programming session.
    For a long busoff (more than 5sec), ECU shall recover and switch to default session.
    """
    dut = Dut()

    start_time = dut.start()

    try:
        dut.precondition(timeout=600)
        result = dut.step(step_1, purpose="Switch to programming session PBL")
        result = result and dut.step(step_2, purpose="Apply a short busoff in programming session "
                                        "PBL and verify ECU stays in programming session PBL")
        result = result and dut.step(step_3, purpose="Apply a long busoff in programming session "
                                        "PBL and verify ECU switch to default session")
        result = result and dut.step(step_4, purpose="Switch to programming session SBL")
        result = result and dut.step(step_5, purpose="Apply a short busoff in programming session "
                                        "SBL and verify ECU stays in programming session SBL")
        result = result and dut.step(step_6, purpose="Apply a long busoff in programming session "
                                        "SBL and verify ECU switch to default session")

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
