"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 488712
version: 0
title: SecOC - Key update handling in ECU
purpose: >
    Define key update process in ECU for writing SecOC key

description: >
    Upon receiving DID 0xD0CA request to write SecOC new key, ECU shall validate the DID, format,
    Access control (Security Access level 0x27), CRC16 checksum, SecOC Cluster Key Identifier,
    decrypt keys (if keys are encrypted format), verify old Key and perform ECU specific update
    protocol (if any) and store the new key.

        There shall be different negative response codes to separate:
          a. Length or format check failed (NRC 0x13: Incorrect message length or invalid format).

          b. ECU is not unlocked with Security Access level 0x27 before requesting write operation
             (NRC 0x33: Security Access denied).

          c. The CRC16 checksum of DID data record fails (NRC 0x31: Request out of range).

          d. SecOC Cluster Key Identifier check: If none of the supported SecOC Cluster Key
             Identifier value(s) stored in ECU match the SecOC Cluster Key Identifier value in the
             DID request, ECU shall send negative response to the DID request with "NRC 0x22-
             conditions not correct".

          e. Failed to decrypt SecOC encrypted key data record when encrypted key format is used
             in DID request (NRC 0x22: Conditions not correct).

          f. SecOC Old key check: ECU shall implement verification method to ensure old key stored
             in ECU and old key sent in DID request are same. If verification fails, ECU shall send
             negative response to DID request with "NRC 0x22(conditions not correct)". The check
             to verify the old key is specific to ECU implementation.

details: >
    Verify different NRCs responded by the ECU on sending DID 0xD0CA request to write SecOC new key
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_test_odtb2 import SupportTestODTB2

SIO = SupportFileIO
SE27 = SupportService27()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()

def prepare_message_with_crc(message, invalid_crc=False):
    """
    Calculate message crc and concatenate to the original message
    Args:
        message (str): message hex string
    Returns:
        message_byte_string (str): message byte string with calculated crc
    """
    if invalid_crc:
        # Generate an invalid crc using default hex string
        crc = SUTE.crc16(bytearray(('FF'*32).encode('utf-8')))
    else:
        # Calculate crc using message hex string
        crc = SUTE.crc16(bytearray(message.encode('utf-8')))

    # Converting calculated crc into hex and removing '0x'
    crc_hex = hex(crc)[2:].upper()
    message_byte_string = bytes.fromhex(message + crc_hex)
    return message_byte_string


def manipulate_key(key, manipulation_byte):
    """
    Manipulate last byte of the key
    Args:
        key (str): key hex string
    Returns:
        manipulation_byte (str): manipulated key hex string
    """
    # Preparing message with invalid old plain text key
    manipulated_key = list(key)
    # Manipulating last byte of old_plain_text_key
    manipulated_key[-2:] = manipulation_byte
    manipulated_key = "".join(manipulated_key)
    return manipulated_key


def secoc_ecu_call(dut: Dut, message, check_nrc, purpose):
    """
    Send request to ECU and validate NRC received
    Args:
        dut (Dut): Dut instance
        message (str): message byte string
        check_nrc (str): NRC code
        purpose (str): purpose of test type
    Returns:
        (bool): True when ECU response with specific NRC
    """
    # Send request to ECU
    response = dut.uds.generic_ecu_call(SC_CARCOM.can_m_send("WriteDataByIdentifier",
                                                              message, b''))

    # Verify NRC for specific test is received correctly
    if response.raw[2:4] =='7F' and response.raw[6:8] == check_nrc:
        logging.info('Received %s NRC for %s as expected', SUTE.pp_can_nrc(check_nrc), purpose)
        return True

    logging.error("Test failed: Expected %s NRC for %s, received %s", SUTE.pp_can_nrc(check_nrc),
                    purpose, response.raw)
    return False


def step_1(dut: Dut, parameters):
    """
    action: Verify NRC for invalid message length

    expected_result: ECU sends NRC 0x13(incorrectMessageLengthOrInvalidFormat)
    """
    # Set ECU to Extended mode
    dut.uds.set_mode(3)

    # Preparing incorrect message length by not adding CRC to message
    message = parameters['secoc_did'] + parameters['secoc_key_attributes'] +\
              parameters['secoc_cluster_key_id'] + parameters['secoc_encryption_iv'] +\
              parameters['secoc_old_plain_text_key'] + parameters['secoc_new_plain_text_key']
    message = bytes.fromhex(message)

    result = secoc_ecu_call(dut, message, check_nrc='13', purpose='incorrect message length')

    return result


def step_2(dut: Dut, parameters):
    """
    action: Verify NRC for sending request without security access

    expected_result: ECU sends NRC 0x33(securityAccessDenied)
    """
    # Preparing message
    message = parameters['secoc_did'] + parameters['secoc_key_attributes'] +\
              parameters['secoc_cluster_key_id'] + parameters['secoc_encryption_iv'] +\
              parameters['secoc_old_plain_text_key'] + parameters['secoc_new_plain_text_key']

    message = prepare_message_with_crc(message)
    result = secoc_ecu_call(dut, message, check_nrc='33', purpose='request without security'
                                                                   ' access')
    return result


def step_3(dut: Dut, parameters):
    """
    action: Verify NRC for invalid crc

    expected_result: ECU sends NRC 0x31(requestOutOfRange)
    """
    # Security access in extended session
    sa_result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config,
                                                        step_no=272, purpose="SecurityAccess")

    if sa_result is False:
        logging.error("Test failed: Security access denied in extended session")
        return False

    # Preparing message with invalid crc
    message = parameters['secoc_did'] + parameters['secoc_key_attributes'] +\
              parameters['secoc_cluster_key_id'] + parameters['secoc_encryption_iv'] +\
              parameters['secoc_old_plain_text_key'] + parameters['secoc_new_plain_text_key']

    message = prepare_message_with_crc(message, invalid_crc=True)

    result = secoc_ecu_call(dut, message, check_nrc='31', purpose='invalid crc')

    return result


def step_4(dut: Dut, parameters):
    """
    action: Verify NRC for invalid cluster key identifier

    expected_result: ECU sends NRC 0x22(conditionsNotCorrect)
    """
    # Preparing message with an invalid cluster key id
    invalid_cluster_key_id = str(int(parameters['secoc_cluster_key_id']))*4
    message = parameters['secoc_did'] + parameters['secoc_key_attributes'] +\
              invalid_cluster_key_id + parameters['secoc_encryption_iv'] +\
              parameters['secoc_old_plain_text_key'] + parameters['secoc_new_plain_text_key']

    message = prepare_message_with_crc(message)

    result = secoc_ecu_call(dut, message, check_nrc='22', \
                              purpose='invalid cluster key identifier')
    return result


def step_5(dut: Dut, parameters):
    """
    action: Verify NRC for invalid encryption data record

    expected_result: ECU sends NRC 0x22(conditionsNotCorrect)
    """
    # Preparing message with an invalid secoc_new_plain_text_key
    manipulated_new_key = manipulate_key(parameters['secoc_new_plain_text_key'], \
                                         manipulation_byte='00')

    message = parameters['secoc_did'] + parameters['secoc_key_attributes'] +\
              parameters['secoc_cluster_key_id'] + parameters['secoc_encryption_iv'] +\
              parameters['secoc_old_plain_text_key'] + manipulated_new_key

    message = prepare_message_with_crc(message)

    result = secoc_ecu_call(dut, message, check_nrc='22', purpose='invalid encryption data record')

    return result


def step_6(dut: Dut, parameters):
    """
    action: Verify NRC for invalid old key record

    expected_result: ECU sends NRC 0x22(conditionsNotCorrect)
    """
    # Preparing message with an invalid secoc_old_plain_text_key
    manipulated_old_key = manipulate_key(parameters['secoc_old_plain_text_key'], \
                                         manipulation_byte='00')

    message = parameters['secoc_did'] + parameters['secoc_key_attributes'] +\
              parameters['secoc_cluster_key_id'] + parameters['secoc_encryption_iv'] +\
              manipulated_old_key + parameters['secoc_new_plain_text_key']

    message = prepare_message_with_crc(message)

    result = secoc_ecu_call(dut, message, check_nrc='22', purpose='invalid old key record')

    return result


def run():
    """
    Verify different NRC messages sent by ECU on sending DID 0xD0CA request to write SecOC new key
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False
    parameters_dict = {'secoc_did': '',
                       'secoc_key_attributes': '',
                       'secoc_cluster_key_id': '',
                       'secoc_encryption_iv': '',
                       'secoc_old_plain_text_key': '',
                       'secoc_new_plain_text_key': ''}

    try:
        dut.precondition(timeout=60)
        # Read yml parameters
        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameter not found")

        result_step = dut.step(step_1, parameters, purpose="Verify NRC for invalid message length")

        if result_step:
            result_step = dut.step(step_2, parameters, purpose="Verify NRC for sending request "
                                                               " without security access")

        if result_step:
            result_step = dut.step(step_3, parameters, purpose="Verify NRC for invalid crc")

        if result_step:
            result_step = dut.step(step_4, parameters, purpose="Verify NRC for invalid key"
                                                               " identifier")

        if result_step:
            result_step = dut.step(step_5, parameters, purpose="Verify NRC for invalid encryption"
                                                               " record")

        if result_step:
            result_step = dut.step(step_6, parameters, purpose="Verify NRC for invalid old key"
                                                               " record")

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
