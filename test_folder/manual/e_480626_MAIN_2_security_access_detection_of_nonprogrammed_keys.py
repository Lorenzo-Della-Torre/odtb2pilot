"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 480626
version: 2
title: : Security Access - detection of non-programmed production keys
purpose: >
    To identify when the initial security access key(s) are still present
    in the ECU, in case of failure when confidential production keys for
    some reasons havent been programmed.

description: >
    The ECU shall report the current status of security access key(s), i.e.
    status indicating if the key has been written according to the requirement
    "Security Access Key programming at OEM" . The information shall be
    accessibleby readDataByIdentifier service using DID “Security Access Key Status”
    DID 0xD09B as defined in the Global Master Reference Database.

    The read only DID shall be possible to read in all sessions
    and it shall not be protected by security access.
    Status “OK, programmed” means that all required security
    access keys per that level are successfully programmed.

    Message direction:   Client <= Server
    Message Type:   Diagnostic response readDataByIdentifier DID Security Access Key Status

    Data byte | Description (all values are in hexadecimal) | Byte Value (Hex)
    --------------------------------------------------------------------------
    #1          Positive Response read request                  62
    #2          DID Security Access Key Status Byte#1 (MSB)     D0
    #3          DID Security Access Key Status Byte#2 (LSB)     9B
    #4          Number of supported Security Access Levels     0x00-0xFF
    #5          First supported security access level          0x00-0xFF,
                                                                odd numbers (security_access_type
                                                                for request seed)
    #6          Status first supported security access level    0x00=programmed
                                                                0x01=not programmed
    …           …
    #n          i:th supported security access level            0x00-0xFF, odd numbers
    #n+1        Status of i:th supported security               0x00, 0x01
    #           access level

    The read only DID shall be possible to read in all sessions and
    it shall not be protected by security access.
    Status “OK, programmed” means that all required security access
    keys per that level are successfully programmed.

    Note.
    If it is agreed by OEM that some key is one-time-programmable at supplier,
    0x00 shall be reported.

details: >
    Verifying if respective security access key are programmed for different access levels in all
    3 diagnostic sessions.
        01 - Diagnostic services in programmingSession, e.g. software download (DID 0xF103)
        05 - Diagnostic services in extendedSession (DID 0xF10A)
        19 - Security Log (DID 0xF115)
        23 - Secure Debug (0xF112)
        27 - Secure On-board Communication (DID 0xF117)
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO

SIO = SupportFileIO()


def verify_levels(response, did, supported_keys):
    """
    Verify security access levels are programmed for respective session
    Args:
        response (dict): ECU response
        did (str): DID 'D09B'
        supported_keys (dict): Security access levels supported in respective session
    Returns:
        return_verify (bool): True if respective security access key are programmed in
                              respective sessions
    """
    true_counter = 0
    return_verify = False

    try:
        if response['sid'] == "62" and response['did'] == did:
            payload = response['details']['item']
            for index in range(2, len(payload)-2, 4):
                security_level = payload[index:index+2]
                programmed_status = int(payload[index+2:index+4], 16)
                if security_level in supported_keys.keys() and \
                    programmed_status == 0:
                    true_counter += 1
                elif programmed_status != 0:
                    logging.info("Security level key: %s - Not Programmed",
                                            supported_keys[security_level])
            return_verify = true_counter == len(supported_keys.keys())
        else:
            return_verify = False
    except KeyError:
        logging.error("Test Failed: Key Error Occurred, DID and/or SID are not present in "
                      "response from ECU")
        return_verify = False
    return return_verify


def step_1(dut: Dut, parameters):
    """
    action: Read DID D09B and verify that the security access keys are programmed in
            default session.
    expected_result: Security access key should indicate programmed(0x00) for all the five
                     levels available in the D09B DID response.
    """
    dut.uds.set_mode(1)
    response = dut.uds.read_data_by_id_22(bytes.fromhex(parameters['did']))
    if response.raw[6:8] == '31':
        logging.error("Test Failed: Unable to read DID - D09B, received NRC31")
        return False

    return verify_levels(response.data, did=parameters['did'],
                         supported_keys=parameters['supported_keys_def'])


def step_2(dut: Dut, parameters):
    """
    action: Read DID D09B and verify that the security access keys are programmed in
            extended session.
    expected_result: Security access key should indicate programmed(0x00) for all the five
                     levels available in the D09B DID response.
    """
    dut.uds.set_mode(3)
    response = dut.uds.read_data_by_id_22(bytes.fromhex(parameters['did']))
    if response.raw[6:8] == '31':
        logging.error("Test Failed: Unable to read DID - D09B, received NRC31")
        return False

    return verify_levels(response.data, did=parameters['did'],
                         supported_keys=parameters['supported_keys_ext'])


def step_3(dut: Dut, parameters):
    """
    action: Read DID D09B and verify that the security access keys are programmed in
            programming session.
    expected_result: Security access key should indicate programmed(0x00) for all the five
                     levels available in the D09B DID response.
    """
    dut.uds.set_mode(2)
    response = dut.uds.read_data_by_id_22(bytes.fromhex(parameters['did']))
    if response.raw[6:8] == '31':
        logging.error("Test Failed: Unable to read DID - D09B, received NRC31")
        return False

    return verify_levels(response.data, did=parameters['did'],
                         supported_keys=parameters['supported_keys_prog'])


def run():
    """
    Verifying if respective security access key are programmed for different access levels in all
    3 diagnostic sessions.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False
    parameters_dict = {'supported_keys_def': {},
                       'supported_keys_ext': {},
                       'supported_keys_prog': {},
                       'did': ''}
    try:
        dut.precondition(timeout=90)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters, purpose="Verify security keys programmed"
                                                           " using DID D09B in default session")
        if result_step:
            result_step = dut.step(step_2, parameters, purpose="Verify security keys programmed"
                                   " using DID D09B in extended session")
        if result_step:
            result_step = dut.step(step_3, parameters, purpose="Verify security keys programmed"
                                   " using DID D09B in programming session")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)

if __name__ == '__main__':
    run()
