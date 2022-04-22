"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 53839
version: 2
title: Protected boot sector
purpose: >
    To avoid unintentional erase of the PBL.

description: >
    The memory area containing the PBL shall be protected from erasure to eliminate the possibility
    of unintentional erasure.

    Note: The protection shall be set up such that it could be removed if a flashable PBL updater
    or special SBL were to be written for this purpose, however the standard SBL or the application
    shall not be able to overwrite or erase the PBL.

details: >
    Verify PBL memory is protected from unintentional erasure.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_service11 import SupportService11
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_test_odtb2 import SupportTestODTB2

SIO = SupportFileIO()
SUTE = SupportTestODTB2()
SE11 = SupportService11()
SE22 = SupportService22()
SE27 = SupportService27()
S_CARCOM = SupportCARCOM()


def flash_in_pbl(dut, memory_start, memory_length):
    """
    Flash in PBL memory address
    Args:
        dut (Dut): An instance of Dut
        memory_start(str): Memory start address
        memory_length(str): Memory length
    Returns:
        (bool): True
    """
    # memory address of PBL: PBL start with the address 80000000 for all ECU
    memory_add = SUTE.pp_string_to_bytes(memory_start, 4)
    # memory size to erase
    memory_size = SUTE.pp_string_to_bytes(memory_length, 4)
    # Prepare payload
    erase = memory_add + memory_size
    payload = S_CARCOM.can_m_send("RoutineControlRequestSID", b'\xFF\x00' + erase, b'\x01')

    response = dut.uds.generic_ecu_call(payload)
    result = SUTE.pp_decode_routine_control_response(response.raw, 'Type1,Aborted')

    if result is False:
        logging.error("Expected 'Type1,Aborted' from ECU")
        return False

    return True


def step_1(dut: Dut):
    """
    action: Change to programming session and Security access to ECU
    expected_result: ECU is in programming session and Security access
                     is granted
    """
    # Change to programming session
    dut.uds.set_mode(2)

    # Security access to ECU
    result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config,
                                                    step_no=272, purpose="SecurityAccess")
    if result:
        logging.error("Security access granted")
        return True

    logging.error("Test failed: Security access denied")
    return False


def step_2(dut: Dut):
    """
    action: Verify flash erase fails on PBL memory location
    expected_result: Flash erase fails on PBL memory
    """
    # Read yml parameters
    parameters_dict = {'pbl_memory_start_address': '',
                       'pbl_memory_write_length': ''}
    parameters = SIO.parameter_adopt_teststep(parameters_dict)

    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameters not found")
        return False

    pbl_memory_start, pbl_memory_length = parameters['pbl_memory_start_address'],\
                                    parameters['pbl_memory_write_length']

    # ECU reply 'Aborted' for flash erase in PBL
    result = flash_in_pbl(dut, pbl_memory_start, pbl_memory_length)

    return result


def step_3(dut):
    """
    action: Verify ECU is in default session
    expected_result: ECU is in default session
    """
    # ECU Hard Reset
    result = SE11.ecu_hardreset_5sec_delay(dut)
    if not result:
        logging.error("Test failed: Unable to reset ECU")
        return False

    # Verify ECU in default session
    result = SE22.read_did_f186(dut, b'\x01')
    if not result:
        logging.error("Test failed: Expected ECU to be in default session")
        return False

    return True


def run():
    """
        Verify PBL memory is protected from unintentional erasure.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=150)

        result_step = dut.step(step_1, purpose="Set to programming session and"
                                               " Security access to ECU")

        if result_step:
            result_step = dut.step(step_2, purpose="Verify flash erase fails on PBL"
                                                   " memory location")

        if result_step:
            result_step = dut.step(step_3, purpose="Verify ECU is in default session")

        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)

if __name__ == '__main__':
    run()
