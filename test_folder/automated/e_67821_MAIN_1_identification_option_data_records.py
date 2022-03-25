"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/


reqprod: 67821
version: 1
title: Identification Option - Vehicle Manufacturer Specific data records

purpose: >
    Volvo Car Corporation defines mandatory data records in GMRDB

description: >
    Identification Option - Vehicle Manufacturer Specific data records
    with data identifiers in the range as specified in the table
    below shall be implemented exactly as they are defined
    in Carcom - Global Master Reference Database.

    Description											    Identifier range
    Identification Option - Vehicle Manufacturer Specific	 0xF100 - 0xF17F
	      											         0xF1A0 - 0xF1EF

    It shall be possible to read the data record by using the
    diagnostic service specified in Ref[LC ; Volvo Car Corporation
    UDS Services - Service 0x22 (ReadDataByIdentifier) Reqs].

details: >

    Reading DIDs form Sddb file within specified range 0xF100 - 0xF17F and 0xF1A0 - 0xF1EF
    respectively in Default session and Programming session & Validate response with service 0x22.
"""


import logging
from hilding.dut import DutTestError
from hilding.dut import Dut
from hilding import get_conf
from supportfunctions.support_file_io import SupportFileIO

SIO = SupportFileIO()


def get_did_from_sddb(sddb_dids_dict):
    """
    Get all DIDs from sddb dictionary into a list
    Args:
    sddb_dids_dict(dictionary) : dictionary of all DIDs from sddb file(pbl, sbl, app)
    Returns: List of all sddb DIDs
    """
    dids_list = []
    # Getting all DIDs from Sddb file
    for did in sddb_dids_dict.keys():
        dids_list.append(did)
    if len(dids_list) == 0:
        logging.error("No DIDs found in sddb dictionary")
    return dids_list


def prepare_lookup_dids(start_did, end_did):
    """
    Prepare lookup DIDs for the specified ranges
    Args:
    start_did(int) : starting DID number
    end_did(int)   : end DID number
    Returns: List of lookup DIDs within the range
    """
    did_list = []
    # Preparing lookup DIDs list with given range
    for did in range(start_did, end_did):
        did_list.append(hex(did)[2:].upper())
    return did_list


def filter_dids(lookup_did_list, sddb_did_list):
    """
    Filtered 0xF100 to 0xF17F and 0xF1A0 to 0xF1EF DIDs from sddb DIDs list
    Args:
        lookup_did_list(list) : lookup DIDs list within the range
        sddb_did_list(list): List of all DIDs from sddb file
    Returns: List of filtered_dids DIDs
    """
    filtered_dids_list = []
    # Getting the DIDs according to the required ranges
    for did in lookup_did_list:
        if did in sddb_did_list:
            filtered_dids_list.append(did)
    if len(filtered_dids_list) == 0:
        logging.error("No valid DIDs found in sddb DIDs list")
    return filtered_dids_list


def step_1(dut: Dut):
    """
    action: Read Sddb file & get all the DIDs, then search and prepare the list of DIDs within
            specified range 0xF100-0xF17F and 0xF1A0-0xF1EF
    expected_result: List of DIDs in range 0xF100-0xF17F and 0xF1A0-0xF1EF.
    """
    # pylint: disable=unused-argument
    filtered_did_dict = {'programming': '',
                         'default': ''}

    conf = get_conf()
    sddb_file = conf.rig.sddb_dids
    if sddb_file is None:
        logging.error('Test Failed: sddb_file is empty')
        return False, None

    sddb_did_list_programming = get_did_from_sddb(sddb_file['pbl_did_dict'])
    sddb_did_list_programming.extend(get_did_from_sddb(sddb_file['sbl_did_dict']))

    if len(sddb_did_list_programming) == 0:
        logging.error('Test Failed: sddb DIDs list empty')
        return False, None

    sddb_did_list_default = get_did_from_sddb(sddb_file['app_did_dict'])

    if len(sddb_did_list_default) == 0:
        logging.error('Test Failed: sddb DIDs list empty')
        return False, None

    # Read yml parameters
    did_range_dict = {'did_range_dict': ''}
    parameters = SIO.parameter_adopt_teststep(did_range_dict)

    if parameters is None:
        logging.error("Test Failed: yml parameter not found")
        return False, None

    # Prepare lookup DIDs list within range F100-F17F
    lookup_did_list = prepare_lookup_dids(int(parameters['did_range_dict']['start_did_f100'], 16),
                                            int(parameters['did_range_dict']['end_did_f17f'], 16))

    # Extend lookup DIDs list within range F1A0-F1EF
    lookup_did_list.extend(prepare_lookup_dids(int(parameters['did_range_dict']['start_did_f1a0'],
                                              16),int(parameters['did_range_dict']['end_did1_f1ef']
                                              , 16)))

    # Filtered programming session SDDB DIDs within range F100-F17F and F1A0-F1EF
    filtered_did_dict['programming'] = filter_dids(lookup_did_list, sddb_did_list_programming)

    # Filtered default session SDDB DIDs within range F100-F17F and F1A0-F1EF
    filtered_did_dict['default'] = filter_dids(lookup_did_list, sddb_did_list_default)

    if filtered_did_dict is None:
        msg = "Test Failed: There is no DIDs available in the sddb file in the \
        range of {} and {}".format(did_range_dict['start_did_f1a0'],did_range_dict['end_did1_f1ef'])
        logging.error(msg)
        return False, None
    return True, filtered_did_dict


def step_2(dut: Dut, filtered_did_dict):
    """
    action: Read all DIDs in default session and compare with response 0x62
    expected_result: Positive response when every DID's response is 0x62.
    """
    # pylint: disable=unused-argument
    result = []
    dut.uds.set_mode(1)

    if len(filtered_did_dict['default']) == 0:
        logging.error("Test Failed: No DIDs found for default session")
        return False

    for did in filtered_did_dict['default']:
        response = dut.uds.read_data_by_id_22(bytes.fromhex(did))
        # Checking 62 in response
        if response.raw[4:6] == '62':
            result.append(True)
            msg = "Positive response: {} received for the DID: {} ".format(response, did)
            logging.info(msg)
        else:
            msg = "Response: {} received for the DID: {}".format(response, did)
            logging.error(msg)
            result.append(False)
    if len(result) != 0 and all(result):
        return True

    logging.error("Test Failed: Received Unexpected response from the ECU for some DID requests"
                  " in Default Session")
    return False



def step_3(dut: Dut, filtered_did_dict):
    """
    action: Read all DIDs in programming session and compare with response 0x62
    expected_result: Positive response when every DID's response is 0x62.
    """
    # pylint: disable=unused-argument
    result = []
    dut.uds.set_mode(2)

    if len(filtered_did_dict['programming']) == 0:
        logging.error("Test Failed: No DIDs found for programming session")
        return False

    for did in filtered_did_dict['programming']:
        response = dut.uds.read_data_by_id_22(bytes.fromhex(did))
        # Checking 62 in response
        if response.raw[4:6] == '62':
            result.append(True)
            msg = "Positive response: {} received for the DID: {} ".format(response, did)
            logging.info(msg)
        else:
            msg = "Response: {} received for the DID: {}".format(response, did)
            logging.error(msg)
            result.append(False)
    if len(result) != 0 and all(result):
        return True

    logging.error("Test Failed: Received Unexpected response from the ECU for some DID requests"
                  " in Programming Session")
    return False


def run():
    """
    Reading DIDs form Sddb file within specified range 0xF100 - 0xF17F and F1A0 - F1EF
    respectively in programming and default session and validate response with service 0x22.
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=60)

        result_step, filtered_did_dict = dut.step(step_1, purpose= "Get DIDs in range "
                                                  "0xF100-0xF17F and 0xF1A0-0xF1EF")

        if result_step:
            result_step = dut.step(step_2, filtered_did_dict, purpose="Reading DIDs in Default "
                                  "session and compare response with service 0x22")
        if result_step:
            result_step = dut.step(step_3, filtered_did_dict,purpose="Reading DIDs in Programming "
                                  "session and compare response with service 0x22")

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
