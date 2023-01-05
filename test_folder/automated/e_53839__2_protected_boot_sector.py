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

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_test_odtb2 import SupportTestODTB2

SIO = SupportFileIO()
SUTE = SupportTestODTB2()
SE27 = SupportService27()
SC_CARCOM = SupportCARCOM()


def step_1(dut: Dut):
    """
    action: Set ECU in programming session and security access
    expected_result: Security access should be successful in programming session
    """
    # Set to programming session
    dut.uds.set_mode(2)

    # Sleep time to avoid NRC-37
    time.sleep(5)

    # Security access to ECU
    result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config)
    if result:
        logging.info("Security access is successful in programming session")
        return True

    logging.error("Test Failed: Security access is denied in programming session")
    return False


def step_2(dut: Dut, parameters):
    """
    action: Flash erase on PBL memory location
    expected_result: Flash erase should be failed on PBL memory location
    """
    memory_start = parameters['pbl_memory_start_address']
    memory_length = parameters['pbl_memory_write_length']

    # memory address of PBL: PBL start with the address 80000000 for all ECU
    memory_add = SUTE.pp_string_to_bytes(memory_start, 4)
    # memory size to erase
    memory_size = SUTE.pp_string_to_bytes(memory_length, 4)

    # Prepare payload
    erase = memory_add + memory_size
    payload = SC_CARCOM.can_m_send("RoutineControlRequestSID", b'\xFF\x00' + erase, b'\x01')

    response = dut.uds.generic_ecu_call(payload)
    result = SUTE.pp_decode_routine_control_response(response.raw, 'Type1,Aborted')

    if result:
        logging.info("Received Type1, Aborted for flash erase on PBL memory location as expected")
        return True

    logging.error("Test Failed: Type1, Aborted is not received for flash erase on PBL memory "
                  "location")
    return False


def step_3(dut: Dut):
    """
    action: ECU hard reset and verify active diagnostic session
    expected_result: ECU should be in default session after ECU reset
    """
    # ECU hard reset
    dut.uds.ecu_reset_1101()

    # Verify active diagnostic session
    response = dut.uds.active_diag_session_f186()
    if response.data["details"]["mode"] == 1:
        logging.info("ECU is in default session after reset as expected")
        return True

    logging.error("Test Failed: Expected ECU should be in default session after reset, but ECU is "
                  "in mode: %s", response.data["details"]["mode"])
    return False


def run():
    """
    Verify PBL memory is protected from unintentional erasure.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'pbl_memory_start_address': '',
                       'pbl_memory_write_length': ''}

    try:
        dut.precondition(timeout=60)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, purpose='Set ECU in programming session and security '
                                               'access')
        if result_step:
            result_step = dut.step(step_2, parameters, purpose='Flash erase on PBL memory '
                                                               'location')
        if result_step:
            result_step = dut.step(step_3, purpose='Verify ECU is in default session after ECU '
                                                   'hard reset')
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
