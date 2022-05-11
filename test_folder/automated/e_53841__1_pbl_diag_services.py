"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 53841
version: 1
title: Primary bootloader diagnostic services
purpose: >
    To define the diagnostic services supported in the primary bootloader.
description: >
    The PBL shall support the diagnostic services required in the programmingSession which are
    specified in [VCC - UDS Services].

details:
    Verify PBL DIDs using readdatabyidentifier(0x22)
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service22 import SupportService22

SIO = SupportFileIO
SE22 = SupportService22()
SE10 = SupportService10()


def step_1(dut: Dut):
    """
    action: Verify ECU is in programming session and read DID EDA0
    expected_result: True on receiving positive response
    """
    # Set to programming session
    SE10.diagnostic_session_control_mode2(dut)
    # Read active diagnostic session
    active_session = SE22.read_did_f186(dut, b'\x02')
    if not active_session:
        logging.error(" ECU not in programming session")
        return False
    result = SE22.read_did_eda0(dut)
    if result:
        logging.info("EDA0 received as expected")
        return True

    logging.error("EDA0 not received")
    return False


def step_2(dut: Dut):
    """
    action: Read Sddb file & get list of PBL DIDs
    expected_result: List of PBL DIDs
    """
    sddb_file = dut.conf.rig.sddb_dids

    if sddb_file is None:
        logging.error('Test Failed: sddb file is empty')
        return False, None

    return True, sddb_file['pbl_did_dict']


def step_3(dut, pbl_did_dict):
    """
    action: Read all DIDs in programming session and compare with response 0x62
    expected_result: Positive response when every DID's response is 0x62.
    """
    pass_or_fail_counter_dict = {"Passed": 0, "Failed": 0, "conditionsNotCorrect (22)": 0,
                                 "requestOutOfRange (31)": 0}
    result_list = list()
    did_counter = 0

    for did_id, did_info in pbl_did_dict.items():
        did_counter += 1

        # Using Service 22 to request a particular DID, returning the result in a dictionary
        did_dict_from_service_22 = SE22.get_did_info(dut, did_id, timeout=2)

        # Copy info to the did_info dictionary from the did_dict
        did_info = SE22.adding_info(did_dict_from_service_22, did_info)

        # Summarizing the result
        info_entry, pass_or_fail_counter_dict = SE22.summarize_result(
            did_info, pass_or_fail_counter_dict, did_id)

        # Add the results
        result_list.append(info_entry)

        # If any of the tests failed. Quit immediately unless debugging.
        if not(info_entry.c_did and info_entry.c_sid and info_entry.c_size):
            logging.info('----------------------')
            logging.info('Testing DID %s failed.', info_entry.did)
            logging.info('----------------------')
            logging.info('DID correct: %s', info_entry.c_did)
            logging.info('SID correct: %s', info_entry.c_sid)
            logging.info('Size correct: %s', info_entry.c_size)
            logging.info('Error message: %s', info_entry.err_msg)
            logging.info('---------------------------------------')

    results=[]
    stepresult = False

    for result in result_list:
        if stepresult == result.c_did and result.c_sid and result.c_size \
                                and not result.err_msg :
            logging.info('DID: %s, c_did: %s, c_sid: %s, c_size: %s, err_msg: %s',
                        result.did, result.c_did, result.c_sid, result.c_size,
                        result.err_msg)

            results.append(stepresult)

    if len(results) != 0 and all(results):
        return True

    logging.error("Test Failed: Received Unexpected response from the ECU for some DID requests "
                  "in Programming Session")
    return False


def step_4(dut: Dut):
    """
    action: Verify ECU is in default session
    expected_result: True on receiving positive response
    """
    # Set to default session
    SE10.diagnostic_session_control_mode1(dut)
    # Read active diagnostic session
    active_session = SE22.read_did_f186(dut, b'\x01')
    if not active_session:
        logging.error("ECU not in default session")
        return False

    logging.info("ECU is in default session")
    return True


def run():
    """
    Reading DIDs form sddb file in programming session and validate response with
    service 0x22
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=60)

        result_step = dut.step(step_1, purpose="Verify ECU is in programming session "
                                               "and EDA0 received as expected")
        if result_step:
            result_step, pbl_did_dict = dut.step(step_2, purpose="Reading DIDs from sddb "
                                                        "file in programming session")
        if result_step:
            result_step = dut.step(step_3, pbl_did_dict, purpose="Reading DIDs in programming "
                                           "session and compare response with service 0x22")
        if result_step:
            result_step = dut.step(step_4, purpose="Verify ECU is in default session")

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
