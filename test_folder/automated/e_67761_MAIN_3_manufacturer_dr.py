"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 67761
version: 3
title: Vehicle manufacturer specific data records defined in GMRDB
purpose: >
    Volvo car corporation defines mandatory data records in GMRDB

description: >
    Data records with data identifiers in the ranges as specified in the table below and shall be
    implemented exactly as they are defined in Carcom - Global Master Reference Database.
    ----------------------------------------------------------------------
    Description	                                      Identifier range
    ----------------------------------------------------------------------
    Vehicle manufacturer specific data records	        0100 - D8FF
                                                        DE00 - E2FF
                                                        E600 - ED1F
                                                        ED80 - ED9F
                                                        F010 - F0FF
    ----------------------------------------------------------------------
    It shall be possible to read the data record by using the diagnostic service specified in
    Ref[LC : Volvo Car Corporation - UDS Services -Service 0x22 (ReadDataByIdentifier) Reqs]

details: >
    Verify all DIDs in application DIDs in sddb within the given range in default session and
    extended session
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_file_io import SupportFileIO

SC = SupportCAN()
SUTE = SupportTestODTB2()
SIO = SupportFileIO()
SE22 = SupportService22()


def read_did_f120(dut, app_diag_part_num):
    """
    Read application diagnostic database part number and compare it with value from sddb
    Args:
        dut(Dut): Dut instance
        app_diag_part_num(str): Application Diagnostic Database Part Number
    Returns:
        (bool): True on successfully verified response with value present in sddb
    """
    dut.uds.read_data_by_id_22(bytes.fromhex('F120'))

    part_number = SUTE.pp_partnumber(SC.can_messages[dut["receive"]][0][2][10:])
    part_number = part_number.replace(" ", "_")
    if part_number == app_diag_part_num :
        logging.info("successfully verified response with value present in sddb")
        return True

    logging.error("Test Failed: Response with value in sddb")
    return False


def prepare_lookup_dids(parameter):
    """
    Prepare lookup DIDs for the specified ranges
    Args:
        parameter(dict): did_list_range
    Returns:
        did_list(list): List of lookup DIDs within the range
    """

    did_list = []
    # Get the length of did_list_range
    no_of_range = len(parameter['did_list_range'])

    # Prepare list of DIDs present in all specified ranges
    for i in range(no_of_range):
        start_did = int(parameter['did_list_range'][i][0], 16)
        end_did = int(parameter['did_list_range'][i][1], 16)
        for did in range(start_did, end_did):
            did_list.append(hex(did)[2:].upper())

    return did_list


def filter_dids(lookup_did_list, app_did_dict):
    """
    Filter DIDs from the given range which are present in the application DIDs from sddb
    Args:
        lookup_did_list(list): Lookup DIDs list within the range
        app_did_dict(dict): application DIDs from sddb
    Returns:
        filtered_dids_list(list): List of filtered DIDs
    """
    filtered_dids_list = []

    for did in lookup_did_list:
        if did in app_did_dict:
            filtered_dids_list.append(did)
    if len(filtered_dids_list) == 0:
        logging.error("No valid DIDs found in sddb DIDs list")

    return filtered_dids_list


def verify_did_response(did_response_list):
    """
    Verify response for all DIDs in filtered_dids_list
    Args:
        did_response_list(list): list of DID responses
    Returns:
        (bool): True when ECU gives expected response for all DIDs
    """
    results=[]

    for result in did_response_list:
        if result.err_msg:
            logging.error('Received error for DID %s: %s', result.did, result.err_msg)

        did_result = result.c_did and result.c_sid and result.c_size and not result.err_msg
        results.append(did_result)

    if len(results) != 0 and all(results):
        logging.info("ECU gives expected response for all DIDs")
        return True

    logging.error("Test Failed: Received unexpected response from the ECU for some DID requests")
    return False


def print_logs_for_failed_did(info_entry):
    """
    Print logs for failed DIDs
    Args:
        info_entry(dut): An instance of Infoentry
    """
    logging.info('----------------------')
    logging.info('Testing DID %s failed.', info_entry.did)
    logging.info('----------------------')
    logging.info('DID correct: %s', info_entry.c_did)
    logging.info('SID correct: %s', info_entry.c_sid)
    logging.info('Size correct: %s', info_entry.c_size)
    logging.info('Error message: %s', info_entry.err_msg)
    logging.info('---------------------------------------')


def verify_diagnostic_service(dut, app_did_dict, parameter):
    """
    Read and verify response for all DIDs in default and extended session by service 22
    Args:
        dut(Dut): Dut instance
        app_did_dict(dict): Dict of DIDs
        parameter(dict): max_no_of_dids, response_timeout
    Returns:
        (bool): True when ECU gives expected response for all DIDs
    """
    max_no_of_dids = int(parameter['max_no_of_dids'])
    response_timeout = int(parameter['response_timeout'])
    pass_or_fail_counter_dict = {"Passed": 0, "Failed": 0, "conditionsNotCorrect (22)": 0,
                                 "requestOutOfRange (31)": 0}
    did_response_list = list()
    did_counter = 0

    lookup_did_list = prepare_lookup_dids(parameter)
    filtered_dids_list = filter_dids(lookup_did_list, app_did_dict)

    for did_id, did_info in app_did_dict.items():

        if did_id in filtered_dids_list:

            did_counter += 1
            if did_counter > max_no_of_dids:
                logging.info("max_no_of_dids reached: %s", max_no_of_dids)
                break
            logging.info('DID counter: %s', str(did_counter))

            logging.info("Testing DID: %s", did_id)
            logging.info(did_info)

            # Using Service 22 to request a particular DID, returning the result in a dictionary
            did_dict_from_service_22 = SE22.get_did_info(dut, did_id, response_timeout)

            # Copy info to the did_info dictionary from the did_dict
            did_info = SE22.adding_info(did_dict_from_service_22, did_info)

            # Summarizing the result
            info_entry, pass_or_fail_counter_dict = SE22.summarize_result(
                did_info, pass_or_fail_counter_dict, did_id)
            if not(info_entry.c_did and info_entry.c_sid and info_entry.c_size):
                print_logs_for_failed_did(info_entry)

            # Add the results
            did_response_list.append(info_entry)

    result = verify_did_response(did_response_list)
    return result


def step_1(dut: Dut):
    """
    action: Read sddb file and get dict of DIDs present in app_did_dict and app_diag_part_num
    expected_result: True when successfully extracted app_did_dict and app_diag_part_num
                     from sddb file
    """
    sddb_file = dut.conf.rig.sddb_dids

    if 'app_did_dict' and 'app_diag_part_num' in sddb_file.keys():
        logging.info("Successfully extracted dict of DIDs present in app_did_dict and "
                     "app_diag_part_num")
        return True, sddb_file['app_did_dict'], sddb_file['app_diag_part_num']

    logging.error("Test Failed: Unable to extract dict of DIDs present in app_did_dict and "
                  "app_diag_part_num")
    return False, None, None


def step_2(dut, app_diag_part_num, app_did_dict, parameters):
    """
    action: Verify all DIDs in app_did_dict within given range in default session
    expected result: True when ECU gives expected response for all DIDs
    """
    # Check active diagnostic session
    result = SE22.read_did_f186(dut, b'\x01')
    if not result:
        logging.error("Test Failed: ECU is not in default session ")
        return False

    logging.info("ECU is in default session as expected")

    result = read_did_f120(dut, app_diag_part_num)
    if result:
        result = verify_diagnostic_service(dut, app_did_dict, parameters)
    return result


def step_3(dut, app_diag_part_num, app_did_dict, parameters):
    """
    action: Verify all DIDs in app_did_dict within given range in default session
    expected result: True when ECU gives expected response for all DIDs
    """
    # Set session in extended
    dut.uds.set_mode(3)

    result = read_did_f120(dut, app_diag_part_num)

    if result:
        result = verify_diagnostic_service(dut, app_did_dict, parameters)

    dut.uds.set_mode(1)
    return result


def run():
    """
    Verify all DIDs in app_did_dict within the given range in default session and extended session
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'did_list_range' : [],
                       'response_timeout' : '',
                       'max_no_of_dids' : ''}

    try:
        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        dut.precondition(timeout = 1200)

        result_step, app_did_dict, app_diag_part_num = dut.step(step_1, purpose="Read sddb file "
                                                                "and get dict of DIDs present "
                                                                "in app_did_dict")
        if result_step:
            result_step = dut.step(step_2, app_diag_part_num, app_did_dict, parameters, purpose=
                                   "Verify all DIDs in app_did_dict within given range in default "
                                   "session")
        if result_step:
            result_step = dut.step(step_3, app_diag_part_num, app_did_dict, parameters, purpose=
                                   "Verify all DIDs in app_did_dict within given range in extended"
                                   " session")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)

    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
