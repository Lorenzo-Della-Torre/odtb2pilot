"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 405174
version: 2
title: Check Memory - verification of programmed data
purpose: >
    The CheckMemory is executed in the ECU via the routineIdentifier(Check Memory).
    This will inform the ECU that a software part is downloaded and that the authenticity
    verification of the stored data shall be started. For some scenarios, the software download
    tools will require two attempts (e.g. for development and production units)

description: >
    The ECU shall start the authenticity verification of programmed data when the routine
    Identifier CheckMemory is received. It shall be possible to make two consecutive CheckMemory
    attempts (i.e. one false attempt is possible). The verification result from the latest
    CheckMemory attempt shall be applied in the ECU. If the CheckMemory verification has failed
    and no more attempts are allowed, a new data transfer of the software part must be performed
    in order to verify the software at a CheckMemory request again. If a third consecutive
    CheckMemory request is sent, that request must be aborted.

    Table - CheckMemory requests shows when two CheckMemory attempts are possible, i.e. that no
    other request is sent in between. To save time, the ECU shall at the second CheckMemory attempt
    reuse the previously performed verifications, e.g. hash calculation.

details: >
    Verifying check memory verification of programmed data
"""

import copy
import logging
from os import listdir
from hilding.dut import DutTestError
from hilding.dut import Dut
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_sec_acc import SecAccessParam
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service31 import SupportService31

SSBL = SupportSBL()
SC = SupportCAN()
SE22 = SupportService22()
SE31 = SupportService31()
SC_CARCOM = SupportCARCOM()


def load_vbf_files(dut):
    """
    Loads the rig specific VBF files found in rigs/<default-rig-name>/VBFs
    Args:
        dut (Dut): An instance of Dut
    Returns:
        boolean: True if vbfs were loaded successfully, otherwise False
    """
    logging.info("~~~~~~~~ Loading VBFs started ~~~~~~~~")
    vbfs = listdir(dut.conf.rig.vbf_path)

    paths_to_vbfs = [str(dut.conf.rig.vbf_path) + "/" + x for x in vbfs]

    if not paths_to_vbfs:
        logging.error("VBFs not found, expected in %s ... aborting", dut.conf.rig.vbf_path)
        return False

    result = SSBL.read_vbf_param(paths_to_vbfs)
    return result


def step_1(dut: Dut):
    """
    action: Activation of SBL and verify ESS software part download no check
    expected_result: True when SBL activation & ESS sw part download no check successful
    """
    # Load vbfs
    vbf_result = load_vbf_files(dut)

    if vbf_result is False:
        logging.error("Aborting software download due to problems when loading VBFs")
        return False, None

    sa_keys: SecAccessParam = dut.conf.default_rig_config
    # Activate SBL
    sbl_result = SSBL.sbl_activation(dut, sa_keys)

    if sbl_result is False:
        logging.error("Aborting software download due to problems when activating SBL")
        return False, None

    result, vbf_header = SSBL.sw_part_download_no_check(dut, SSBL.get_ess_filename(),
                                                                stepno=1)

    if result :
        logging.info("ESS software part download no check successful")
        return True, vbf_header

    logging.error("Test Failed: ESS software part download no check not successful")
    return False, None


def step_2(dut: Dut, vbf_header):
    """
    action: 1st check memory with verification failed
    expected_result: True when the signed data could not be authenticated
    """
    vbf_header_manipulate = copy.deepcopy(vbf_header)
    vbf_header_manipulate["sw_signature_dev"] = int(str(vbf_header_manipulate\
                                                ["sw_signature_dev"])[:-2]+ '16')

    result = SE31.check_memory(dut, vbf_header_manipulate, 2)

    if result and SSBL.pp_decode_routine_check_memory(SC.can_messages[dut["receive"]][0][2])\
                  == 'The signed data could not be authenticated':
        logging.info(SSBL.pp_decode_routine_check_memory(SC.can_messages[dut["receive"]][0][2]))
        return True

    logging.error("Test Failed: check_memory failed and decode routine check memory %s ",
                   SSBL.pp_decode_routine_check_memory(SC.can_messages[dut["receive"]][0][2]))
    return False


def step_3(dut: Dut, vbf_header):
    """
    action: 2nd check memory with verification failed
    expected_result: True when the signed data could not be authenticated
    """
    vbf_header_manipulate = copy.deepcopy(vbf_header)
    vbf_header_manipulate["sw_signature_dev"] = int(str(vbf_header_manipulate\
                                                         ["sw_signature_dev"])[:-2]+ '14')
    result = SE31.check_memory(dut, vbf_header_manipulate, 3)

    if result and SSBL.pp_decode_routine_check_memory(SC.can_messages[dut["receive"]][0][2])\
            == 'The signed data could not be authenticated':
        logging.info(SSBL.pp_decode_routine_check_memory(SC.can_messages[dut["receive"]][0][2]))
        return True

    logging.error("Test Failed: check_memory failed and decode routine check memory %s ",
                   SSBL.pp_decode_routine_check_memory(SC.can_messages[dut["receive"]][0][2]))
    return False


def step_4(dut: Dut, vbf_header):
    """
    action: Verify 3rd check memory with negative response
    expected_result: True when negative response NRC 31 received
    """
    vbf_header_manipulate = copy.deepcopy(vbf_header)
    sw_signature = vbf_header_manipulate['sw_signature_dev'].to_bytes(
        (vbf_header_manipulate['sw_signature_dev'].bit_length()+7) // 8, 'big')

    # Prepare payload
    payload = SC_CARCOM.can_m_send("RoutineControlRequestSID", b'\x02\x12' + sw_signature, b'')
    response = dut.uds.generic_ecu_call(payload)

    if response.raw[2:8] == "7F3131":
        logging.info("Received NRC-31(requestOfRange) as expected")
        return True
    logging.error("Test Failed: Expected NRC-31(requestOfRange) received, %s", response.raw)
    return False


def step_5(dut: Dut):
    """
    action: Download ESS software part no check
    expected_result: True when positive response from ECU
    """
    logging.info("ESS Software part download no check")
    result = SSBL.sw_part_download_no_check(dut, SSBL.get_ess_filename(), stepno=5)

    if result :
        logging.info("ESS software part download no check successful")
        return True

    logging.error("Test Failed: ESS software part download no check not successful")
    return False


def step_6(dut: Dut, vbf_header):
    """
    action: 1st Check memory with verification failed
    expected_result: True when The signed data could not be authenticated
    """
    vbf_header_manipulate = copy.deepcopy(vbf_header)
    vbf_header_manipulate["sw_signature_dev"] = int(str(vbf_header_manipulate\
                                                            ["sw_signature_dev"])[:-2]+ '16')

    result = SE31.check_memory(dut, vbf_header_manipulate, 6)
    if result and SSBL.pp_decode_routine_check_memory(SC.can_messages[dut["receive"]][0][2])\
                                    == 'The signed data could not be authenticated':
        logging.info(SSBL.pp_decode_routine_check_memory(
                         SC.can_messages[dut["receive"]][0][2]))
        return True

    logging.error("Test Failed: check_memory failed and decode routine check memory %s ",
                   SSBL.pp_decode_routine_check_memory(SC.can_messages[dut["receive"]][0][2]))
    return False


def step_7(dut: Dut, vbf_header):
    """
    action: Verify response time P4server_max for the 2nd check memory routine is 2000 ms
    expected_result: True when response time P4server_max for the positive check memory response
                     is within 2000 ms
    """
    result = SE31.check_memory(dut, vbf_header, 7)

    response_time = dut.uds.milliseconds_since_request()
    # p4_server_max_time  is 2000ms
    if response_time <= 2000:
        logging.info("Response time %sms is less than or equal to 2000ms(p4_server_max_time) as"
                     "expected", response_time)

        if result and SSBL.pp_decode_routine_check_memory(SC.can_messages[dut["receive"]][0][2])\
            == 'The verification is passed':

            logging.info(SSBL.pp_decode_routine_check_memory\
                        (SC.can_messages[dut["receive"]][0][2]))
            return True

        logging.error("Test Failed: check_memory failed and decode routine check memory %s ",
                SSBL.pp_decode_routine_check_memory(SC.can_messages[dut["receive"]][0][2]))
        return False

    logging.error("Test Failed: Response time %s ms is greater than 2000ms",
                   response_time)
    return False


def step_8(dut: Dut):
    """
    action: Verify sw part download and complete & compatible routine
    expected_result: True when complete compatible routine and sw part download successful
    """
    for swp in SSBL.get_df_filenames():
        result = SSBL.sw_part_download(dut, swp, stepno=8)

    result = result and SSBL.check_complete_compatible_routine(dut, stepno=8)
    result = result and (SSBL.pp_decode_routine_complete_compatible(
                         SC.can_messages[dut["receive"]][0][2]) == 'Complete, Compatible')
    return result


def step_9(dut: Dut):
    """
    action: Reset ECU and verify ECU is in default session
    expected_result: True when ECU  is in default session
    """
    # ECU hard reset
    response = dut.uds.ecu_reset_1101()
    if response.raw[2:4] == '51':
        check_default = SE22.read_did_f186(dut, dsession=b'\x01')
        if check_default:
            logging.info("ECU is in default session as expected")
            return True

        logging.error("Test Failed: ECU is not in default session")
        return False

    logging.error("Test Failed: ECU reset failed")
    return False


def run():
    """
    Verifying check memory - verification of programmed data
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=700)
        result_step , vbf_header = dut.step(step_1, purpose="Verify activation of SBL and ESS"
                                                            " software part download no check")
        if result_step:
            result_step = dut.step(step_2, vbf_header, purpose="Verify 1st check memory with "
                                                               "verification failed")
        if result_step:
            result_step = dut.step(step_3, vbf_header, purpose="Verify 2nd check memory with"
                                                               " verification failed")
        if result_step:
            result_step = dut.step(step_4, vbf_header, purpose="Verify 3rd check memory with"
                                                               " negative response")
        if result_step:
            result_step = dut.step(step_5, purpose="Verify download ESS software part no check")

        if result_step:
            result_step = dut.step(step_6, vbf_header, purpose="Verify 1st check memory with"
                                                               " verification failed")
        if result_step:
            result_step = dut.step(step_7, vbf_header, purpose="Verify response time P4server_max"
                                                   " for the 2nd check memory routine is 2000 ms")
        if result_step:
            result_step = dut.step(step_8, purpose="Verify sw part download, complete"
                                                    " and compatible routine")
        if result_step:
            result_step = dut.step(step_9, purpose="Reset ECU and Verify ECU in default session")

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
