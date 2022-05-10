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
from hilding import get_conf
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
    sddb_did_list_programming = []

    conf = get_conf()
    sddb_file = dut.conf.rig.sddb_dids

    if sddb_file is None:
        logging.error('Test Failed: sddb file is empty')
        return False, None
   
    sddb_did_list_programming = list(sddb_file['pbl_did_dict'].keys())
   
    if len(sddb_did_list_programming) == 0:
        logging.error('Test Failed: PBL DIDs list not received')
        return False, None
    logging.info("PBL DIDs list received")
    return True, sddb_did_list_programming


def step_3(dut: Dut, sddb_did_list_programming):
    """
    action: Read all DIDs in programming session and compare with response 0x62
    expected_result: Positive response when every DID's response is 0x62.
    """
    results = []

    for did in sddb_did_list_programming:
        response = dut.uds.read_data_by_id_22(bytes.fromhex(did))

        # Checking 62 in response
        if response.raw[2:4] != '62':           
            logging.error("Expected positive response 62, received %s", response.raw[2:4])
            return False

        pos = response.raw.find('did')
        if response.raw[pos:pos+2] == 'did':
            logging.info("Received positive response 62 for DID %s ", response.raw[pos:pos+2])
            results.append(True)

        logging.error("Expected positive response 62, received %s, for DID %s",
                       response.raw[2:4], response.raw[pos:pos+2])
        results.append(False)
            
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
            result_step, sddb_did_list_programming = dut.step(step_2, purpose="Reading DIDs from "
                                         "sddb file in programming session and making list of it")
        if result_step:
            result_step = dut.step(step_3, sddb_did_list_programming, purpose="Reading DIDs in "
                                  "programming session and compare response with service 0x22")
        if result_step:
            result_step = dut.step(step_4, purpose="Verify ECU is in default session")

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()

    