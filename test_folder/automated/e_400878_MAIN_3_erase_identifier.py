"""

/*********************************************************************************/



Copyright © 2023 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 400878
version: 3
title: Erase Identifier - restrictions
purpose: >
    To ensure that a complete logical block is erased is required for several purposes:
        (1) To ensure that all information about validity status is always erased (if part of the
    logical block). Otherwise, implicitly knowledge of the bootloader implementation is required
    to ensure that it is erased.
        (2) No unknown data is stored in the addressed logical block, i.e. previously installed
    data deleted ("uninstalled).
        (3) It will also enable simplified off-board review of the logical block definitions, by
    checking that the erase identifier is identical to the expected logical block.

description: >
    The erase identifier range(s) of the software part header must match a valid logical block.
    The ECU shall at an eraseMemory request verify that the erase startAddress and Length matches
    a logical block range, otherwise the ECU shall abort the request. If the eraseMemory request
    is valid, the ECU must ensure that the complete memory for the addressed logical block is
    erased.

details: >
    Verify negative response with NRC-31 for RoutineControlRequestSID (flash erase) with wrong
    length and wrong start address.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_SBL import SupportSBL

S_CARCOM = SupportCARCOM()
SSBL = SupportSBL()


def get_vbf_header():
    """
    Extract vbf header from vbf file
    Args:
        None
    Returns:
        vbf_header (dict): Vbf header
    """
    ess_file = SSBL.get_ess_filename()
    vbf_header = SSBL.read_vbf_file(ess_file)[1]
    SSBL.vbf_header_convert(vbf_header)

    return vbf_header


def step_1(dut: Dut):
    """
    action: SBL activation
    expected_result: SBL activation should be is successful
    """
    SSBL.get_vbf_files()
    result = SSBL.sbl_activation(dut, sa_keys=dut.conf.default_rig_config)
    if result:
        logging.info("SBL activation is successful")
        return True

    logging.error("Test Failed: SBL activation is failed")
    return False


def step_2(dut: Dut):
    """
    action: Verify negative response with NRC-31 for RoutineControlRequestSID with wrong start
            address
    expected_result: ECU should send negative response with NRC-31(requestOutOfRange)
    """
    vbf_header = get_vbf_header()
    vbf_erase = vbf_header['erase'][0]
    # Extract start address
    start_address = vbf_header['erase'][0][0]
    # Modify start address
    modified_address = start_address + 1

    payload = S_CARCOM.can_m_send("RoutineControlRequestSID", bytes.fromhex('FF00') +
                                   modified_address.to_bytes(4, byteorder='big') +
                                   vbf_erase[1].to_bytes(4, byteorder='big'), b'\x01')
    response = dut.uds.generic_ecu_call(payload)
    if response.raw[2:8]=='7F3131':
        logging.info("Received negative response with NRC-31 for routine control request "
                     "as expected")
        return True

    logging.error("Test Failed: Expected NRC-31, but received %s", response.raw)
    return False


def step_3(dut: Dut):
    """
    action: Verify negative response with NRC-31 for RoutineControlRequestSID with wrong length
    expected_result: ECU should send negative response with NRC-31(requestOutOfRange)
    """
    vbf_header = get_vbf_header()
    vbf_erase = vbf_header['erase'][0]
    # Extract length
    length = vbf_header['erase'][0][1]
    # Modify length
    modified_length = length + 1

    payload = S_CARCOM.can_m_send("RoutineControlRequestSID", bytes.fromhex('FF00') +
                                   vbf_erase[0].to_bytes(4, byteorder='big') +
                                   modified_length.to_bytes(4, byteorder='big'), b'\x01')
    response = dut.uds.generic_ecu_call(payload)
    if response.raw[2:8]=='7F3131':
        logging.info("Received negative response with NRC-31 for routine control request "
                     "as expected")
        return True

    logging.error("Test Failed: Expected NRC-31, but received %s", response.raw)
    return False


def step_4(dut: Dut):
    """
    action: Verify negative response with NRC-31 for RoutineControlRequestSID with wrong start
            address and wrong length
    expected_result: ECU should send negative response with NRC-31(requestOutOfRange)
    """
    vbf_header = get_vbf_header()
    # Extract start address
    start_address = vbf_header['erase'][0][0]
    # Modify start address
    modified_address = start_address + 1

    # Extract length
    length = vbf_header['erase'][0][1]
    # Modify length
    modified_length = length + 1

    payload = S_CARCOM.can_m_send("RoutineControlRequestSID", bytes.fromhex('FF00') +
                                   modified_address.to_bytes(4, byteorder='big') +
                                   modified_length.to_bytes(4, byteorder='big'), b'\x01')
    response = dut.uds.generic_ecu_call(payload)
    if response.raw[2:8]=='7F3131':
        logging.info("Received negative response with NRC-31 for routine control request "
                     "as expected")
        return True

    logging.error("Test Failed: Expected NRC-31, but received %s", response.raw)
    return False


def step_5(dut: Dut):
    """
    action: ECU reset and verify default session
    expected_result: ECU should be in default session
    """
    # ECU hard reset
    dut.uds.ecu_reset_1101()

    # Verify default session
    response = dut.uds.active_diag_session_f186()
    if response.data["details"]["mode"] == 1:
        logging.info("ECU is in default session as expected")
        return True

    logging.error("Test Failed: Expected ECU in default session, but it is in mode %s",
                  response.data["details"]["mode"])
    return False


def run():
    """
    Verify negative response with NRC-31 for RoutineControlRequestSID (flash erase) with wrong
    length and wrong start address.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=120)

        result_step = dut.step(step_1, purpose="SBL activation")
        if result_step:
            result_step = dut.step(step_2, purpose="Verify negative response with NRC-31 for "
                                   "RoutineControlRequestSID with wrong start address")
        if result_step:
            result_step = dut.step(step_3, purpose="Verify negative response with NRC-31 for "
                                   "RoutineControlRequestSID with wrong length")
        if result_step:
            result_step = dut.step(step_4, purpose="Verify negative response with NRC-31 for "
                                   "RoutineControlRequestSID with wrong start address and wrong "
                                   "length")
        if result_step:
            result_step = dut.step(step_5, purpose="ECU reset and verify default session")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
