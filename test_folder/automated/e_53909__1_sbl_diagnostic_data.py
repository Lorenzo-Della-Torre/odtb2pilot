"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 53909
version: 1
title: Secondary bootloader diagnostic data
purpose: >
    To define the diagnostic data supported in the secondary bootloader.

description: >
   The SBL shall support the diagnostic data required in programmingSession which are specified
   in [VCC - UDS Data].

details: >
    Compare the SBL part number from SBL and SDDB and verify if all DIDs in DB
    are present in SW SBL
"""

import logging
import hilding.flash as swdl
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service11 import SupportService11
from supportfunctions.support_file_io import SupportFileIO

SC = SupportCAN()
SUTE = SupportTestODTB2()
SE11 = SupportService11()
SE22 = SupportService22()
SIO = SupportFileIO()


def step_1(dut: Dut, parameters):
    """
    action: Download and activate SBL and compare the SBL part number from SBL and SDDB
    expected_result: SBL part numbers from SDDB and ECU should be equal
    """
    # Loads the rig specific VBF files
    vbf_result = swdl.load_vbf_files(dut)
    if not vbf_result:
        return False

    # Download and activate SBL on the ECU
    sbl_result = swdl.activate_sbl(dut)
    if not sbl_result:
        logging.error("Test Failed: SBL activation failed")
        return False

    response = dut.uds.read_data_by_id_22(bytes.fromhex(parameters['sbl_db_part_number']))
    if response.raw[4:6] != '62':
        logging.error("Test Failed: Expected positive response 62 for DID %s, received %s",
                       parameters['sbl_db_part_number'], response.raw)
        return False

    logging.info("Successfully read DID %s with positive response %s",
                 parameters['sbl_db_part_number'], response.raw[4:6])

    # SBL part number from active SBL
    valid_number = parameters['sbl_db_part_number']+'_valid'
    sbl_part_number = response.data['details'][valid_number]

    # SBL part number from SDDB
    sbl_diag_part_num = dut.conf.rig.sddb_dids["sbl_diag_part_num"]

    # Replace " " by  "_" in SBL part number read from active SBL
    sbl_part_number = sbl_part_number.replace(" ", "_")
    result = bool(sbl_diag_part_num == sbl_part_number)

    if not result:
        logging.error("Test Failed: SBL part numbers are not equal")
        logging.error("Test Failed: SBL part number from SDDB %s", sbl_diag_part_num)
        logging.error("Test Failed: SBL part number from active SBL %s", sbl_part_number)
    else:
        logging.info("SBL part numbers are equal as expected")

    return result


def step_2(dut: Dut, parameters):
    """
    action: Verify if all DIDs in DB are present in SW SBL
    expected_result: ECU should give positive response for all the DIDs in DB
    """
    sbl_did_dict = dut.conf.rig.sddb_dids["sbl_did_dict"]

    pass_or_fail_counter_dict = {"Passed": 0,
                                 "Failed": 0,
                                 "conditionsNotCorrect (22)": 0,
                                 "requestOutOfRange (31)": 0}
    result_list = list()
    did_counter = 0
    stepresult = len(sbl_did_dict) > 0

    for did_id, did_info in sbl_did_dict.items():
        did_counter += 1

        if did_counter > parameters['max_no_of_dids']:
            logging.info("max_no_of_dids reached: %s", parameters['max_no_of_dids'])
            break

        # Using Service 22 to request a particular DID, returning the result in a dictionary
        did_dict_from_service_22 = SE22.get_did_info(dut, did_id, parameters['response_timeout'])

        # Copy info to the did_info dictionary from the did_dict
        did_info = SE22.adding_info(did_dict_from_service_22, did_info)

        # Summarizing the result
        info_entry, pass_or_fail_counter_dict = SE22.summarize_result(did_info,
                                                pass_or_fail_counter_dict, did_id)
        # Add the results
        result_list.append(info_entry)

        # Log if any of the tests failed.
        if not(info_entry.c_did and info_entry.c_sid and info_entry.c_size):
            logging.info('----------------------')
            logging.info('Testing DID %s failed.', info_entry.did)
            logging.info('----------------------')
            logging.info('DID correct: %s', info_entry.c_did)
            logging.info('SID correct: %s', info_entry.c_sid)
            logging.info('Size correct: %s', info_entry.c_size)
            logging.info('Error message: %s', info_entry.err_msg)
            logging.info('---------------------------------------')

    logging.info("DIDs checked: %s", did_counter)
    logging.info("Summary of dids checked %s", pass_or_fail_counter_dict)

    if stepresult:
        for result in result_list:
            stepresult = stepresult and result.c_did and result.c_sid and result.c_size and\
                        not result.err_msg
    return stepresult


def step_3(dut: Dut, parameters):
    """
    action: Verify if DIDs not in DB return error message
    expected_result: ECU should give NRC-31(requestOutOfRange) for DIDs not in DB
    """
    response = dut.uds.read_data_by_id_22(bytes.fromhex(parameters['did_not_in_db']))

    if response.raw[2:4] == '7F' and response.raw[6:8] == '31':
        logging.info("Successfully read DID %s with negative response %s and NRC %s",
                      parameters['did_not_in_db'], response.raw[2:4], response.raw[6:8])
        return True

    logging.error("Test Failed: Expected negative response 7F and NRC 31 for DID %s,"
                  " received %s", parameters['did_not_in_db'], response.raw)
    return False


def step_4(dut: Dut):
    """
    action: Verify ECU hardreset
    expected_result: ECU should be in default session after ECU hardreset
    """
    # ECU reset
    result = SE11.ecu_hardreset_5sec_delay(dut)
    if not result:
        return False

    # Verify active diagnostic session
    result = SE22.read_did_f186(dut, dsession=b'\x01')
    if not result:
        logging.error("Test Failed: ECU is not in default session")
        return False

    logging.info("ECU is in default session as expected")
    return True


def run():
    """
    Compare the SBL part number from SBL and SDDB and verify if all DIDs in DB
    are present in SW SBL
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'response_timeout' : 0,
                       'max_no_of_dids' : 0,
                       'did_not_in_db' : '',
                       'sbl_db_part_number' : ''}
    try:
        dut.precondition(timeout=150)

        # Read periodic did from yml file
        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameter not found")

        result_step = dut.step(step_1, parameters, purpose='Download and activate SBL and compare'
                                                           ' the SBL part number from SBL and'
                                                           ' SDDB')
        if result_step:
            result_step = dut.step(step_2, parameters, purpose='Verify if all DIDs in DB are'
                                                               ' present in SW SBL')
        if result_step:
            result_step = dut.step(step_3, parameters, purpose='Verify if DIDs not in data base'
                                                               ' return Error message')
        if result_step:
            result_step = dut.step(step_4, purpose='Verify ECU hardreset')
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
