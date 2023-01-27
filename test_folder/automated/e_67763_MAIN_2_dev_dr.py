"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 67763
version: 2
title: Development specific data records - implementer specified
purpose: >
	ECU Specific data records are not supported by Volvo Car Corporation tools and must be
    defined in a separate identifier range.

description: >
    If data records that are needed only during the development of the ECU are defined by the
    implementer, these data records shall have data identifiers in the ranges as specified in
    the table below:
    ------------------------------------------------------------------------------------------
    Description                                                          Identifier range
    ------------------------------------------------------------------------------------------
    Development specific data records - Implementer specified             D900 - DCFF
                                                                          E300 - E4FF
                                                                          EE00 - EFFF
    ------------------------------------------------------------------------------------------
    • It shall be possible to read the data record by using the diagnostic service specified in
      Ref[LC : Volvo Car Corporation - UDS Services -Service 0x22 (ReadDataByIdentifier) Reqs]

details: >
    Compare the APP software part number with SDDB software part number and also verify if all
    the data base DIDs are present in software APP for default and extended session
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_file_io import SupportFileIO

SC = SupportCAN()
SUTE = SupportTestODTB2()
SE22 = SupportService22()
SIO = SupportFileIO()


def activate_sa_compare_part_no(dut, parameters):
    """
    Activate security access request sid and compare the APP part number from DID response and SDDB
    Args:
        dut (Dut): An instance of dut
        parameters (dict): APP data base part number
    Returns:
        (bool): True when APP part numbers are equal
    """
    # Extract SWP Number for APP
    response = dut.uds.read_data_by_id_22(bytes.fromhex(parameters['app_db_part_number']))
    if response.raw[4:6] != '62':
        logging.error("Test Failed: Expected positive response 62 for DID %s, received %s",
                       parameters['app_db_part_number'], response.raw)
        return False

    logging.info("Successfully read DID %s with positive response %s",
                  parameters['app_db_part_number'], response.raw[4:6])

    # APP part number from APP
    app_part_number = SUTE.pp_partnumber(SC.can_messages[dut["receive"]][0][2][10:])

    # APP part number from SDDB
    app_diag_part_num = dut.conf.rig.sddb_dids["app_diag_part_num"]

    # Replace " " by  "_" in APP part number read from APP
    app_part_number = app_part_number.replace(" ", "_")

    if app_diag_part_num == app_part_number:
        logging.info("APP part numbers are equal as expected")
        return True

    logging.error("Test Failed: APP part number %s is not equal with SDDB APP part number %s",
                   app_part_number, app_diag_part_num)
    return False


def verify_db_dids(dut, parameters):
    """
    Verify if all data base DIDs are present in software APP
    Args:
        dut (Dut): An instance of dut
        parameters (dict): Maximum number of dids and response timeout
    Returns:
        (bool): True when positive response of all the DB DIDs
    """
    app_did_dict = dut.conf.rig.sddb_dids["app_did_dict"]

    pass_or_fail_counter_dict = {"Passed": 0,
                                 "Failed": 0,
                                 "conditionsNotCorrect (22)": 0,
                                 "requestOutOfRange (31)": 0}
    result_list = list()
    did_counter = 0
    stepresult = len(app_did_dict) > 0

    for did_id, did_info in app_did_dict.items():

        if ((0xD900 <= int(did_id, base=16) <= 0xDCFF) or
            (0xE300 <= int(did_id, base=16) <= 0xE4FF) or
            (0xEE00 <= int(did_id, base=16) <= 0xEFFF)):

            did_counter += 1
            if did_counter > parameters['max_no_of_dids']:
                logging.info("Maximum number of DIDs reached: %s", parameters['max_no_of_dids'])
                break

            # Using Service 22 to request a particular DID, returning the result in a dictionary
            did_dict_from_service_22 = SE22.get_did_info(dut, did_id,
                                       parameters['response_timeout'])

            # Copy info to the did_info dictionary from the did_dict
            did_info = SE22.adding_info(did_dict_from_service_22, did_info)

            # Summarizing the result
            info_entry, pass_or_fail_counter_dict = SE22.summarize_result(did_info,
                                                    pass_or_fail_counter_dict, did_id)
            # Add the results
            result_list.append(info_entry)

            # Log if any of the tests failed
            if not(info_entry.c_did and info_entry.c_sid and info_entry.c_size):
                logging.error('Testing DID %s failed.', info_entry.did)
                logging.error('DID correct: %s', info_entry.c_did)
                logging.error('SID correct: %s', info_entry.c_sid)
                logging.error('Size correct: %s', info_entry.c_size)
                logging.error('Error message: %s', info_entry.err_msg)

    logging.info("DIDs checked: %s", did_counter)
    logging.info("Summary of DIDs checked %s", pass_or_fail_counter_dict)

    if stepresult:
        for result in result_list:
            stepresult = stepresult and result.c_did and result.c_sid and result.c_size and\
                         not result.err_msg
    return stepresult


def step_1(dut: Dut, parameters):
    """
    action: Compare the APP software part number with SDDB software part number and also verify
            if all the data base DIDs are present in software APP for default session
    expected_result: True when successfully verified all the data base DIDs are present in
                     software APP
    """
    result = activate_sa_compare_part_no(dut, parameters)
    if not result:
        return False

    result = verify_db_dids(dut, parameters)
    if not result:
        return False

    return True


def step_2(dut: Dut, parameters):
    """
    action: Compare the APP software part number with SDDB software part number and also verify
            if all the data base DIDs are present in software APP for extended session
    expected_result: True when successfully verified all the data base DIDs are present in
                     software APP
    """
    # Set to extended session
    dut.uds.set_mode(3)

    # Verify active diagnostic session
    response = dut.uds.active_diag_session_f186()
    if response.data["details"]["mode"] != 3:
        logging.error("Test Failed: ECU is not in extended session")
        return False

    result = activate_sa_compare_part_no(dut, parameters)
    if not result:
        return False

    result = verify_db_dids(dut, parameters)
    if not result:
        return False

    return True


def run():
    """
    Compare the APP software part number with SDDB software part number and also verify if all
    the data base DIDs are present in software APP for default and extended session
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'response_timeout' : 0,
                       'max_no_of_dids' : 0,
                       'app_db_part_number' : ''}
    try:
        dut.precondition(timeout=1000)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameter not found")

        result_step = dut.step(step_1, parameters, purpose='Compare the APP software part number'
                               ' with SDDB software part number and also verify if all the data'
                               ' base DIDs are present in software APP for default session')
        if result_step:
            result_step = dut.step(step_2, parameters, purpose='Compare the APP software part'
                                   ' number with SDDB software part number and also verify if all'
                                   ' the data base DIDs are present in software APP for extended'
                                   ' session')
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
