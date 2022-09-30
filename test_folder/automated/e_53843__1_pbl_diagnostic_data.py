"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 53843
version: 1
title: Primary bootloader diagnostic data
purpose: >
	To define the diagnostic data supported in the primary bootloader.

description: >
   The PBL shall support the diagnostic data required in the programmingSession which are
   specified in [VCC - UDS Data].

details: >
    Compare the PBL software part number with SDDB software part number and also verify if all
    the data base DIDs are present in software PBL
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_service31 import SupportService31
from supportfunctions.support_file_io import SupportFileIO

SE22 = SupportService22()
SE27 = SupportService27()
SE31 = SupportService31()
SIO = SupportFileIO()


def step_1(dut: Dut, parameters):
    """
    action: Activate security access request sid and compare the PBL part number from PBL and SDDB
    expected_result: PBL part number from DID response should be equal to PBL part number from SDDB
    """
    # Verify programming preconditions
    result = SE31.routinecontrol_requestsid_prog_precond(dut, stepno=111)
    if not result:
        return False

    # Set programming session
    dut.uds.set_mode(2)

    # Sleep time to avoid NRC37
    time.sleep(5)

    # Security Access Request SID
    result =  SE27.activate_security_access_fixedkey(dut, dut.conf.default_rig_config)
    if not result:
        return False

    # Extract SWP Number for PBL
    response = dut.uds.read_data_by_id_22(bytes.fromhex(parameters['pbl_db_part_number']))
    if response.raw[4:6] != '62':
        logging.error("Test Failed: Expected positive response 62 for DID %s, received %s",
                       parameters['pbl_db_part_number'], response.raw)
        return False

    logging.info("Successfully read DID %s with positive response %s",
                  parameters['pbl_db_part_number'], response.raw[4:6])

    # PBL part number from PBL
    valid_number = parameters['pbl_db_part_number']+'_valid'
    pbl_part_number = response.data['details'][valid_number]

    # PBL part number from SDDB
    pbl_diag_part_num = dut.conf.rig.sddb_dids["pbl_diag_part_num"]

    # Replace " " by  "_" in PBL part number read from PBL
    pbl_part_number = pbl_part_number.replace(" ", "_")

    if pbl_diag_part_num == pbl_part_number:
        logging.info("PBL part numbers are equal as expected")
        return True

    logging.error("Test Failed: PBL part number %s is not equal with SDDB PBL part number %s",
                   pbl_part_number, pbl_diag_part_num)
    return False


def step_2(dut: Dut, parameters):
    """
    action: Request all PBL DIDs in SDDB for ECU and Verify if all DIDs in DB are present in SW PBL
    expected_result: ECU should give positive response for all the DB DIDs present in software PBL
    """
    pbl_did_dict = dut.conf.rig.sddb_dids['pbl_did_dict']

    pass_or_fail_counter_dict = {"Passed": 0,
                                 "Failed": 0,
                                 "conditionsNotCorrect (22)": 0,
                                 "requestOutOfRange (31)": 0}
    result_list = list()
    did_counter = 0
    stepresult = len(pbl_did_dict) > 0

    for did_id, did_info in pbl_did_dict.items():
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
    logging.info("Summary of DIDs checked %s", pass_or_fail_counter_dict)

    if stepresult:
        for result in result_list:
            stepresult = stepresult and result.c_did and result.c_sid and result.c_size and\
                        not result.err_msg
    return stepresult


def step_3(dut: Dut, parameters):
    """
    action: Read DID and verify DIDs are not in database
    expected_result: ECU should give NRC-31(requestOutOfRange) for DIDs not in database
    """
    response = dut.uds.read_data_by_id_22(bytes.fromhex(parameters['did_not_in_db']))

    if response.raw[2:4] == '7F' and response.raw[6:8] == '31':
        logging.info("Successfully read DID %s with negative response %s and NRC %s",
                      parameters['did_not_in_db'], response.raw[2:4], response.raw[6:8])
        return True

    logging.error("Test Failed: Expected negative response 7F and NRC 31 for DID %s,"
                  " received %s", parameters['did_not_in_db'], response.raw)
    return False


def run():
    """
    Compare the PBL software part number with SDDB software part number and also verify if all
    the data base DIDs are present in software PBL
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'response_timeout' : 0,
                       'max_no_of_dids' : 0,
                       'did_not_in_db' : '',
                       'pbl_db_part_number' : ''}
    try:
        dut.precondition(timeout=150)

        # Read periodic did from yml file
        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameter not found")

        result_step = dut.step(step_1, parameters, purpose='Activate security access request sid'
                               ' and compare the PBL part number from PBL and SDDB')
        if result_step:
            result_step = dut.step(step_2, parameters, purpose='Verify if all data base DIDs are'
                                   ' present in software PBL')
        if result_step:
            result_step = dut.step(step_3, parameters, purpose='Verify DIDs are not in database')

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
