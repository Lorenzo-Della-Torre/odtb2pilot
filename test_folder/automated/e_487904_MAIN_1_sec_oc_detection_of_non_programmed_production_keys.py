"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 487904
version: 1
title: SecOC - Detection of non-programmed production keys
purpose: >
    To identify when the initial SecOC key(s) are still present in the ECU, in case of failure
    when confidential production keys for some reasons haven't been programmed.

description: >
    The ECU shall report the current status of all supported SecOC keys, i.e. status indicating
    if the keys are in initial state or has been programmed with keys other than initial keys.
    The information shall be accessible by readDataByIdentifier service using
    DID 0xD0CB - “Secure On-board Communication Key Write Status” as defined in the GMRDB.

    The format of SecOC key(s) status, represented in hexadecimal, when read from ECU shall be
    concatenation of one byte long total number of SecOC keys supported in ECU and the sequence of
    two bytes long supported SecOC Cluster Key Identifier, one-byte long status of key related
    to SecOC Cluster Key Identifier. The sequence of key status in response shall be reported
    for all supported SecOC Cluster Key Identifiers in ECU.

    The read only DID shall be possible to read in all sessions except programming session and
    it shall not be protected by security access.

    Status “OK, programmed” for each supported SecOC Cluster Key Identifier means that respective
    SecOC key is successfully programmed with key other than initial value.
    Status “not programmed” for each SecOC Cluster Key Identifier means initial or no key exists
    in ECU for respective key identifier.

    Note.
    If it is agreed by OEM that production key(s) is programmed at supplier, 0x00 shall be reported

details: >
    Read did 'D0CB' and Verify all supported SecOC keys are programmed or not programmed.
    Steps-
        1. Read D0CB and verify positive response 0x62
        2. Calculate number of SecOC key and verify all supported SecOC keys are programmed(00)
           or not programmed(01).
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO

SIO = SupportFileIO()


def verify_supported_sec_oc_keys_status(response, status_key_pos):
    """
    Verify the status of supported SecOC keys is Programmed(00) or not programmed(01)
    Args:
        response(str): ECU response
        status_key_pos(int): Status of supported SecOC key position
    Returns:
        (bool): Successfully verified supported SecOC key status 00(programmed)
    """
    result = False
    if response[status_key_pos:status_key_pos+2] == '00':
        logging.info("Supported SecOC key status %s (programmed)",
                      response[status_key_pos:status_key_pos+2])
        result = True
    elif response[status_key_pos:status_key_pos+2] == '01':
        logging.error("Test Failed: Supported SecOC key status %s (not programmed)",
                      response[status_key_pos:status_key_pos+2])
        result = False

    return result

def verify_supported_sec_oc_keys(response, parameters):
    """
    Verify supported SecOc keys
    Args:
        response(str): DID response
        parameters(dict): SecOC keys id and positions
    Returns: True on successfully verified all the SecOC keys and status
    """
    # Extract and calculate number of supported SecOC keys
    sec_oc_keys_count = int((response[6:8]), 16)
    logging.info("Number of supported SecOC keys are %s :", sec_oc_keys_count)

    results = []
    # First SecOC key status position
    status_key_pos = parameters['secoc_status_pos']
    # First SecOC key id position
    key_id_pos = parameters['secoc_key_id_pos']

    for _ in range(sec_oc_keys_count):
        if response[key_id_pos:status_key_pos] == parameters['supported_sec_oc_key_id']:
            logging.info("Valid supported SecOC key id %s is received",
                          response[key_id_pos:status_key_pos])
            results.append(verify_supported_sec_oc_keys_status(response, status_key_pos))
            status_key_pos = status_key_pos + 6
            key_id_pos = key_id_pos + 6
        else:
            logging.error("Supported SecOC key id %s is invalid",
                          response[key_id_pos:status_key_pos])
            results.append(False)

    if all(results) and len(results) != 0:
        return True

    return False


def step_1(dut: Dut):
    """
    action: Read did 'D0CB' (Secure on board communication - key write status) and
            verify the current status of all supported SecOC keys in default session
    expected_result: True on successfully read did 'D0CB' and verify Status of
                     supported SecOC Keys (programmed or not programmed)
    """
    # Read yml parameters
    parameters_dict = {'did': '',
                       'supported_sec_oc_key_id': '',
                       'secoc_status_pos': 0,
                       'secoc_key_id_pos': 0}
    parameters = SIO.parameter_adopt_teststep(parameters_dict)

    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False, None, None

    # Set to default session
    dut.uds.set_mode(1)

    result = False
    # Read did 'D0CB'(Secure on board communication - key write status)
    response = dut.uds.read_data_by_id_22(bytes.fromhex(parameters['did']))

    # Compare positive response
    if response.raw[0:2] == '62':
        logging.info("Successfully read DID: %s with positive response %s",
                     parameters['did'], response.raw[0:2])
        result = verify_supported_sec_oc_keys(response.raw, parameters)
        if not result:
            logging.error("Test Failed: SecOC key status verification failed")
            return False, None

        return True, parameters

    logging.error("Test Failed: Expected positive response 62 for DID: %s, received %s",
                  parameters['did'], response.raw)
    return False, None


def step_2(dut: Dut, parameters):
    """
    action: Read did 'D0CB' (Secure on board communication - key write status) and
            verify the current status of all supported SecOC keys in extended session
    expected_result: True on successfully read did 'D0CB' and verify Status of
                     supported SecOC Keys (programmed or not programmed)
    """
    # Set to extended session
    dut.uds.set_mode(3)

    result = False
    # Read did 'D0CB'(Secure on board communication - key write status)
    response = dut.uds.read_data_by_id_22(bytes.fromhex(parameters['did']))

    # Compare positive response
    if response.raw[0:2] == '62':
        logging.info("Successfully read DID: %s with positive response %s",
                     parameters['did'], response.raw[0:2])
        result = verify_supported_sec_oc_keys(response.raw, parameters)
        if not result:
            logging.error("Test Failed: SecOC key status verification failed")
            return False, None

        return True, parameters

    logging.error("Test Failed: Expected positive response 62 for DID: %s, received %s",
                  parameters['did'], response.raw)
    return False


def run():
    """
    Read did 'D0CB' and Verify all supported SecOC keys are programmed or not programmed
    in both default and extended session
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=60)

        result_step, parameters = dut.step(step_1, purpose="Read did 'D0CB' and verify the "
                                           "current status of all supported SecOC keys in "
                                           "default session")
        if result_step:
            result_step = dut.step(step_2, parameters,  purpose="Read did 'D0CB' and verify "
                                   "the current status of all supported SecOC keys in "
                                   "extended session")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
