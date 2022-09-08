"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 53854
version: 1
title: Support of erase and write data to non-volatile memory
purpose: >
    Only the Secondary Bootloader (SBL) shall be able to erase and write data to the
    non-volatile memory.

description: >
    The Secondary Bootloader shall upon request erase and write data to the ECU non-volatile
    memory, except for the non-volatile memory area containing the primary bootloader.

details: >
    Verify PBL fails to erase and write data to the non-volatile memory
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN, CanMFParam
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_service11 import SupportService11
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_service31 import SupportService31
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_SBL import SupportSBL

SC = SupportCAN()
SC_CARCOM = SupportCARCOM()
SIO = SupportFileIO()
SE11 = SupportService11()
SE27 = SupportService27()
SE31 = SupportService31()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()


def change_control_frame_parameters(dut):
    """
    Request to change frame control delay
    Args:
        dut (Dut): An instance of Dut
    Return: None
    """
    can_mf: CanMFParam = {"block_size": 0,
                          "separation_time": 0,
                          "frame_control_delay": 0,
                          "frame_control_flag": 48,
                          "frame_control_auto": True}

    SC.change_mf_fc(dut["receive"], can_mf)


def pbl_flash_erase(dut, memory_start, memory_length):
    """
    Flash erase in PBL memory address
    Args:
        dut (Dut): An instance of Dut
        memory_start (str): Memory start address
        memory_length (str): Memory length
    Return:
        response.raw (str): ECU response
    """
    # Memory address of PBL: PBL start with the address 80000000 for all ECU
    memory_add = SUTE.pp_string_to_bytes(memory_start, 4)

    # Memory size to erase
    memory_size = SUTE.pp_string_to_bytes(memory_length, 4)

    # Prepare payload
    erase = memory_add + memory_size
    payload = SC_CARCOM.can_m_send("RoutineControlRequestSID", bytes.fromhex('FF00')+ erase,
                                    bytes.fromhex('01'))
    change_control_frame_parameters(dut)

    response = dut.uds.generic_ecu_call(payload)
    return response.raw


def step_1(dut: Dut):
    """
    action: Verify programming preconditions and security access in programming session
    expected_result: True when security access is successful in programming session
    """
    # Verify programming preconditions
    result = SE31.routinecontrol_requestsid_prog_precond(dut)
    if not result:
        logging.error("Test Failed: Routine control requestsid prog preconditions unsuccessful")
        return False

    #Sleep time to avoid NRC37
    time.sleep(5)

    # Set to programming session
    dut.uds.set_mode(2)

    # Security access
    sa_result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config)
    if not sa_result:
        logging.error("Test Failed: Security access denied in programming session")
        return False

    logging.info("Security access successful in programming session")
    return True


def step_2(dut: Dut, parameters):
    """
    action: Request flash erase in PBL
    expected_result: True on receiving 'Type1,Aborted' response
    """
    # Request for flash erase in PBL
    response = pbl_flash_erase(dut, memory_start=parameters['pbl_memory_start_address'],
                               memory_length=parameters['pbl_memory_write_length'])
    result  = SUTE.pp_decode_routine_control_response(response, 'Type1,Aborted')
    if result:
        logging.info("Received flash erase routine reply aborted in PBL as expected")
        return True

    logging.error("Test Failed: Received unexpected response %s", response)
    return False


def step_3(dut: Dut):
    """
    action: Download and activate SBL
    expected_result: True when successfully activated SBL
    """
    # Loads the rig specific VBF files
    vbf_result = SSBL.get_vbf_files()
    if not vbf_result:
        logging.error("Test Failed: Aborting due to problems when loading VBFs")
        return False

    # Download SBL
    result, vbf_sbl_header = SSBL.sbl_download(dut, SSBL.get_sbl_filename())
    if not result:
        logging.error("Test Failed: SBL download failed")
        return False

    # Activate SBL
    sbl_result = SSBL.activate_sbl(dut, vbf_sbl_header, stepno=2)
    if not sbl_result:
        logging.error("Test Failed: SBL activation failed")
        return False

    logging.info("SBL activation successful")
    return True


def step_4(dut: Dut, parameters):
    """
    action: Verify flash erase of PBL memory address is not allowed
    expected_result: True when received negative response '7F' and NRC-31(requestOutOfRange)
    """
    # Request for flash erase in PBL memory address
    response = pbl_flash_erase(dut, memory_start=parameters['pbl_memory_start_address'],
                               memory_length=parameters['pbl_memory_write_length'])
    result = SUTE.test_message(SC.can_messages[dut["receive"]], teststring='7F3131')
    if not result:
        logging.error("Test Failed: Expected negative response '7F' and NRC-31(requestOutOfRange), "
                      "received %s", response)
        return False

    logging.info("Received negative response %s and NRC-%s as expected", response[2:4],
                  response[6:8])
    return True


def step_5(dut: Dut):
    """
    action: ECU hard reset
    expected_result: True when ECU is in default session
    """
    # ECU hard reset
    result = SE11.ecu_hardreset_5sec_delay(dut)
    if not result:
        logging.error("Test Failed: Unable to reset ECU")
        return False

    # Verify active diagnostic session
    response = dut.uds.active_diag_session_f186()
    if not response.data["details"]["mode"] == 1:
        logging.error("Test Failed: ECU is not in default session")
        return False

    logging.info("ECU is in default session as expected")
    return True


def run():
    """
    Verify PBL fails to erase and write data to the non-volatile memory
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'pbl_memory_start_address': '',
                       'pbl_memory_write_length': ''}
    try:
        dut.precondition(timeout=90)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, purpose='Verify programming preconditions and'
                                               ' security access in programming session')
        if result_step:
            result_step = dut.step(step_2, parameters, purpose='Request flash erase in PBL')
        if result_step:
            result_step = dut.step(step_3, purpose='Download and activate SBL')
        if result_step:
            result_step = dut.step(step_4, parameters, purpose='Verify flash erase of PBL memory'
                                                               ' address is not allowed')
        if result_step:
            result_step = dut.step(step_5, purpose='ECU hard reset')
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
