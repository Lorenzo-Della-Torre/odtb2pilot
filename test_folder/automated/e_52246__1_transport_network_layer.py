"""

/*********************************************************************************/



Copyright © 2023 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 52246
version: 1
title: : Transport_Network Layer
purpose: >
    To define the transport/network layer used by the bootloader.

description: >
    The CAN bootloader shall implement the transport/network layer defined in LC VCC DoCAN.

details: >
    Verify the transport/network layer used by the bootloader.
    Steps:
        1. Verify programming preconditions
        2. Verify ECU in primary bootloader
        3. ECU reset and verify active diagnostic session
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service31 import SupportService31
from supportfunctions.support_service27 import SupportService27

SE22 = SupportService22()
SE31 = SupportService31()
SE27 = SupportService27()


def step_1(dut: Dut):
    """
    action: Verify programming preconditions
    expected_result: Routine control request and security access should be successful in
                     programming session
    """
    result = SE31.routinecontrol_requestsid_prog_precond(dut)
    if not result:
        logging.error("Test Failed: Routine control request failed")
        return False

    # Set to programming session
    dut.uds.set_mode(2)

    # Sleep time to avoid NRC-37
    time.sleep(5)

    # Security access to ECU
    security_access = SE27.activate_security_access_fixedkey(dut,
                                                             sa_keys=dut.conf.default_rig_config)
    if not security_access:
        logging.error("Test Failed: Security access denied in programming session")
        return False

    logging.info("Security access successful in programming session")
    return True


def step_2(dut: Dut):
    """
    action: Verify ECU is in primary bootloader
    expected_result: ECU should be in primary bootloader
    """
    result = SE22.verify_pbl_session(dut)
    if not result:
        logging.error("Test Failed: ECU is not in primary bootloader")
        return False

    logging.info("ECU is in primary bootloader")
    return True


def step_3(dut: Dut):
    """
    action: ECU hard reset and verify ECU in default session
    expected_result: ECU should be in default session
    """
    # ECU hard reset
    reset_result = dut.uds.ecu_reset_1101()
    time.sleep(5)
    result = reset_result and SE22.read_did_f186(dut, dsession=b'\x01')
    if not result:
        logging.error("Test Failed: ECU is not in default session")
        return False

    logging.info("ECU is in default session as expected")
    return True


def run():
    """
    Verify the transport/network layer used by the bootloader.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=60)

        result_step = dut.step(step_1, purpose="Verify programming preconditions")
        if result_step:
            result_step = dut.step(step_2, purpose="Verify ECU is in primary bootloader")
        if result_step:
            result_step = dut.step(step_3, purpose="ECU hard reset and verify ECU in default"
                                                   " session")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
