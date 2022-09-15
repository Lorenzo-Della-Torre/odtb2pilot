"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 487907
version: 1
title: : SecOC - Key Sync Test Diagnostics
purpose: >
    Define diagnostics to enable diagnostic clients to perform Secure On-board Communication key
    sync test in order to verify same key is provisioned in all ECUs in SecOC cluster

description: >
    ECU shall support control routine identifier, 0x0234, as defined in GMRDB. RID shall be
    supported only in extended diagnostic session and Security Access level 0x27 must be unlocked
    to perform SecOC key sync test operation.

    The format of the routine control option record for SecOC key sync test RID start routine
    request shall be two bytes long SecOC Cluster Key Identifier value represented in hexadecimal.

    Upon Routine control start routine request, ECU shall check if requested SecOC Cluster Key
    Identifier is supported by ECU. For a valid SecOC Cluster Key Identifier, ECU shall respond
    back with requested key identifier concatenated with 128-bit Message Authentication Code (MAC)
    value computed using AES-128 CMAC algorithm on pre-configured 16-byte static constant value
    "0xFFFF 5A5A 5A5A 5A5A 5A5A 5A5A 5A5A FFFF" as input with corresponding key of SecOC Cluster
    Key Identifier requested in RID start routine request option record.

    The format of Routine status record for SecOC key sync test RID start routine response from ECU
    shall be concatenation of two bytes long SecOC Cluster Key Identifier value and 16 Bytes long
    Message Authentication Code represented in hexadecimal.

    There shall be different negative response codes to separate:
        1. Length or format check failed (NRC 0x13: Incorrect message length or invalid format)
        2. ECU is not unlocked with security access level 0x27 before requesting the Key sync test
           operation (NRC 0x33: Security Access denied)
        3. SecOC Cluster Key Identifier check: If none of the supported SecOC Cluster Key
           Identifier value(s) stored in ECU match the SecOC Cluster Key Identifier value
           in RID request, ECU shall send a negative response to the RID request with "NRC 0x31:
           Request out of range".
        4. Error in computing Message Authentication Code in ECU
           (NRC 0x72: General programming failure)

details: >
    Verify diagnostic response of RoutineControl RID Secure On-board Communication Key Sync
    Testcontrol and also verify different NRCs responded by the ECU on sending routine control
    request with RID 0x0234.
"""

import logging
from Crypto.Hash import CMAC
from Crypto.Cipher import AES
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_test_odtb2 import SupportTestODTB2

SC = SupportCAN()
SC_CARCOM = SupportCARCOM()
SIO = SupportFileIO
SE27 = SupportService27()
SUTE = SupportTestODTB2()


def request_diagnostic_routine_control(dut, parameters):
    """
    Request RoutineControl(0x31) and get the ECU response
    Args:
        dut(Dut): Dut instance
        parameters(dict): routine id, SecOC cluster key id
    Returns:
        response.raw (str): ECU response of RoutineControl(0x31) request
    """
    # Create a payload with routine identifier(0x0234) and SecOC cluster key identifier(0x0001)
    payload = SC_CARCOM.can_m_send("RoutineControlRequestSID", b'\x01'
                                   + bytes.fromhex(parameters['routine_id'])
                                   + bytes.fromhex(parameters['sec_oc_cluster_key_id'])
                                   , b'')
    # Send a request with created payload
    response = dut.uds.generic_ecu_call(payload)

    return response.raw


def calculate_authentication_data(pre_config_16_byte_value, message):
    """
    Calculate message authentication data using Crypto AES-128-CMAC algorithm
    Args:
        pre_config_16_byte_value(str): Pre-configured 16-byte static constant value
        message(str): ECU response excluding MAC
    Returns:
        calculated_cmac(str): Calculated authentication data
    """
    key_128 = bytes.fromhex(pre_config_16_byte_value)
    cipher_obj = CMAC.new(key_128, ciphermod=AES)
    cipher_obj.update(bytes.fromhex(message))
    calculated_cmac = cipher_obj.hexdigest().upper()

    return calculated_cmac


def check_cluster_keyid_and_mac(rid_response, parameters):
    """
    Verify SecOC cluster key id and message authentication code(MAC)
    Args:
        rid_response (str): ECU response of RoutineControl(0x31) request
        parameters (dict): SecOC cluster key id, pre-configured 16-byte static constant value
    Returns:
        (bool): True when received valid SecOC cluster key id & message authentication code
    """
    # rid_response[10:14] gives SecOC cluster key id
    if rid_response[10:14] == parameters['sec_oc_cluster_key_id']:
        logging.info("Received valid SecOC Cluster Key id %s as expected", rid_response[10:14])

        calulated_cmac = calculate_authentication_data(parameters['pre_config_16_byte_value'],
                                                       message=rid_response[0:14])
        # rid_response[14:46] gives message authentication code (MAC)
        if rid_response[14:46] == calulated_cmac:
            logging.info("Received valid MAC value %s as expected", rid_response[14:46])
            return True

        logging.error("Test Failed: Expected valid MAC value %s, received %s", calulated_cmac,
                      rid_response[14:46])
        return False

    logging.error("Test Failed: Expected valid SecOC Cluster Key id %s, received %s",
                   parameters['sec_oc_cluster_key_id'], rid_response[10:14])
    return False


def check_nrc(response, nrc_code, purpose):
    """
    Validate NRC for specific test
    Args:
        response(str): ECU response of RoutineControl(0x31) request
        nrc_code(str): NRC code
        purpose(str): purpose of test type
    Returns:
        (bool): True when ECU response with specific NRC
    """
    if response[2:4] =='7F' and response[6:8] == nrc_code:
        logging.info('Received %s NRC for %s as expected', SUTE.pp_can_nrc(nrc_code), purpose)
        return True

    logging.error("Test Failed: Expected %s NRC for %s, received %s", SUTE.pp_can_nrc(nrc_code),
                   purpose, response)
    return False


def step_1(dut: Dut, parameters):
    """
    action: Verify NRC for sending request without security access
    expected_result: ECU sends NRC 0x33(securityAccessDenied)
    """
    # Set to extended session
    dut.uds.set_mode(3)

    # Send routine control request without security access
    response = request_diagnostic_routine_control(dut, parameters)

    # Verify NRC-33 (SecurityAccessDenied)
    result = check_nrc(response, nrc_code='33', purpose='request without security access')

    return result


def step_2(dut: Dut):
    """
    action: Security access to ECU in extended session
    expected_result: Security access successful
    """
    sa_result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config,
                                                       step_no=272, purpose="SecurityAccess")
    if sa_result:
        logging.info("Security access successful in extended session")
        return True

    logging.error("Test Failed: Security access denied in extended session")
    return False


def step_3(dut: Dut, parameters):
    """
    action: Verify diagnostic response of RoutineControl RID Secure On-board Communication Key
            Sync Testcontrol
    expected_result: True when the bytes of routine control response verified successfully
    """
    rid_response = request_diagnostic_routine_control(dut, parameters)

    # rid_response[2:4] gives positive response code '71'
    if rid_response[2:4] == '71':
        logging.info("Received positive response %s for routine identifier(0x0234) as expected",
                      rid_response[2:4])
        result = SUTE.pp_decode_routine_control_response(SC.can_messages[dut["receive"]][0][2],
                                                         'Type1,Completed')
        # rid_response[8:10] gives RoutineInfo Byte
        if result and rid_response[8:10] == '10':
            logging.info("RoutineInfo Byte %s represents RoutineType: 'Type1' & Routine Status: "
                         "'Completed' as expected", rid_response[8:10])

            result = check_cluster_keyid_and_mac(rid_response, parameters)
            return result

        logging.error("Test Failed: Expected RoutineInfo Byte '10', received %s",
                       rid_response[8:10])
        return False

    logging.error("Test Failed: Expected positive response for routine identifier(0x0234),"
                  " received %s", rid_response)
    return False


def step_4(dut: Dut, parameters):
    """
    action: Verify NRC for incorrect message length or invalid format
    expected_result: ECU sends NRC 0x13(incorrectMessageLengthOrInvalidFormat)
    """
    # Preparing incorrect message length by not adding SecOC cluster key id to payload
    payload = SC_CARCOM.can_m_send("RoutineControlRequestSID", b'\x01'
                                   + bytes.fromhex(parameters['routine_id'])
                                   , b'')
    # Send a request with invalid payload
    response = dut.uds.generic_ecu_call(payload)

    # Verify NRC-13 (IncorrectMessageLengthOrInvalidFormat)
    result = check_nrc(response.raw, nrc_code='13', purpose='incorrect message length')

    return result


def step_5(dut: Dut, parameters):
    """
    action: Verify NRC for invalid cluster key id
    expected_result: ECU sends NRC 0x31(RequestOutOfRange)
    """
    # Create a payload with routine identifier(0x0234) and invalid SecOC cluster key id(0x0002)
    payload = SC_CARCOM.can_m_send("RoutineControlRequestSID", b'\x01'
                                  + bytes.fromhex(parameters['routine_id'])
                                  + bytes.fromhex(parameters['invalid_sec_oc_cluster_key_id'])
                                  , b'')
    # Send a request with invalid payload
    response = dut.uds.generic_ecu_call(payload)

    # Verify NRC-31 (RequestOutOfRange)
    result = check_nrc(response.raw, nrc_code='31', purpose='invalid cluster key id')

    return result


def run():
    """
    Verify diagnostic response of RoutineControl RID Secure On-board Communication Key Sync
    Testcontrol and also verify different NRCs responded by the ECU on sending routine control
    request with RID 0x0234.
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'routine_id': '',
                       'sec_oc_cluster_key_id': '',
                       'pre_config_16_byte_value': '',
                       'invalid_sec_oc_cluster_key_id': ''}

    try:
        dut.precondition(timeout=60)
        # Read yml parameters
        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters, purpose="Verify NRC for sending request without"
                                                           " security access")
        if result_step:
            result_step = dut.step(step_2, purpose="Security access to ECU in extended session")
        if result_step:
            result_step = dut.step(step_3, parameters, purpose="Verify diagnostic response of "
                                                               "RoutineControl RID Secure "
                                                               "On-board Communication Key Sync "
                                                               "Testcontrol")
        if result_step:
            result_step = dut.step(step_4, parameters, purpose="Verify NRC for incorrect message "
                                                               "length or invalid format")
        if result_step:
            result_step = dut.step(step_5, parameters, purpose="Verify NRC for invalid cluster "
                                                               "key id")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
