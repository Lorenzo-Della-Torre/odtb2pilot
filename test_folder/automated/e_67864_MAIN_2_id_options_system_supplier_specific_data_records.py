"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 67864
version: 2
title: Identification Options-System Supplier Specific data records
purpose: >
    System supplier specific data records are not supported by Volvo Car Corporation tools and must
    be defined in a separate identifier range.

description: >
    If Identification Options data records, that are not for used by Volvo Car Corporation, are
    defined by the system supplier, these data records shall have data identifiers in the range as
    specified in the table below:

    Description	                             Identifier range
    Development specific data records	     F1F0 - F1FF

    •	It may be possible to read the data record by using the diagnostic service specified
        Ref[LC : Volvo Car Corporation - UDS Services -Service 0x22 (ReadDataByIdentifier) Reqs]

details:
    Reading DIDs form sddb file within specified range 0xF1F0 - 0xF1FF and validate response
    with service ReadDataByIdentifier(0x22)
"""

import logging
from hilding.dut import DutTestError
from hilding.dut import Dut
from supportfunctions.support_file_io import SupportFileIO

SIO = SupportFileIO()


def filter_dids(lookup_did_list, app_did_dict):
    """
    Filter 0xF1F0 to 0xF1FF from application DIDs in sddb
    Args:
        lookup_did_list(list) : lookup DIDs list within the range F1F0-F1FF
        app_did_dict(dict): Dict of DIDs
    Returns:
        (list): Filtered DIDs list
    """
    filtered_dids_list = []
    # Getting DIDs according to the required range
    for did in lookup_did_list:
        if did in app_did_dict.keys():
            filtered_dids_list.append(did)

    return filtered_dids_list


def step_1(dut: Dut):
    """
    action: Read sddb file and get the application DIDs dictionary
    expected_result: List of application DIDs
    """
    sddb_file = dut.conf.rig.sddb_dids
    if 'app_did_dict' in sddb_file.keys():
        logging.info("Successfully extracted dictionary of application DIDs")

        return True, sddb_file['app_did_dict']

    logging.error("Test Failed: Unable to extract dictionary of application DIDs")
    return False, None


def step_2(dut: Dut, app_did_dict, parameters):
    """
    action: Filter 0xF1F0 to 0xF1FF from application DIDs dictionary
    expected_result: List of DIDs between range 0xF1F0-0xF1FF
    """
    # pylint: disable=unused-argument

    lookup_did_list =[]
    # Preparing lookup DIDs list with range F1F0-F1FF
    for did in range(int(parameters['start_did_f1f0'], 16), int(parameters['end_did_f1ff'], 16)):
        lookup_did_list.append(hex(did)[2:].upper())

    # Filter application DIDs within range F1F0-F1FF
    filtered_dids_list = filter_dids(lookup_did_list, app_did_dict)

    if len(filtered_dids_list) != 0:
        return True, filtered_dids_list
    logging.error("Test Failed: No DIDs available in the sddb file between range %s-%s",
                   parameters['start_did_f1f0'], parameters['end_did_f1ff'])
    return False, None


def step_3(dut: Dut, filtered_dids_list):
    """
    action: Read all DIDs between range F1F0-F1FF and verify response is 0x62 using service
            ReadDataByIdentifier(0x22)
    expected_result: Positive response when every DID's response is 0x62
    """
    result = []
    dut.uds.set_mode(1)

    for did in filtered_dids_list:
        response = dut.uds.read_data_by_id_22(bytes.fromhex(did))
        # Checking 62 and respective did in response
        if response.raw[4:6] == '62'and response.raw[6:10] == did:
            logging.info("Received positive response %s for DID %s", response.raw, did)
            result.append(True)
        else:
            logging.error("Test Failed: Expected positive response 62, received %s for %s DID",
                          response.raw, did)
            result.append(False)
    if len(result) != 0 and all(result):
        logging.info("Received expected positive response for all DID requests")
        return True

    logging.error("Test Failed: Received Unexpected response from the ECU for some DID requests")
    return False


def run():
    """
    Reading DIDs from sddb file within specified range 0xF1F0 - 0xF1FF
    and verify positive response for service ReadDataByIdentifier(0x22)
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'start_did_f1f0':'',
                       'end_did_f1ff':''}
    try:
        dut.precondition(timeout=60)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step, app_did_dict= dut.step(step_1, purpose= "Read application DIDs from sddb")

        if result_step:
            result_step, filtered_dids_list = dut.step(step_2, app_did_dict, parameters,
                                                       purpose="Filter DIDs for range F1F0-F1FF")
        if result_step:
            result_step = dut.step(step_3, filtered_dids_list, purpose="Verify response of DIDs "
                                   "for range F1F0-F1FF with service ReadDataByIdentifier(0x22)")

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
