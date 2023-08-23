"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 480617
version: 1
title: Security Access message structures

purpose: >
    Define message structures, for authentication method 0x0001.

description: >
    The message structures of clientRequestSeed, serverResponseSeed, clientSendKey and
    serverResponseKey shall be:

    struct client_request_seed {
    uint8_t sa_request_sid;
    uint8_t sa_type;
    uint16_t message_id;
    uint16_t authentication_method ;
    unsigned char iv[16];
    unsigned char encrypted_data_record[16];
    unsigned char auth_data[16] ;
    };

    struct server_response_seed {
    uint8_t sa_response_sid;
    uint8_t sa_type;
    uint16_t message_id;
    unsigned char iv [16];
    unsigned char encrypted_data_record [32];
    unsigned char auth_data [16];
    };

    struct client_send_key {
    uint8_t sa_request_sid;
    uint8_t sa_type;
    uint16_t message_id;
    unsigned char iv[16];
    unsigned char encrypted_data_record[16];
    unsigned char auth_data[16];
    };

    struct server_response_key {
    uint8_t sa_response_sid;
    uint8_t sa_type;
    };

    The client and server must always verify and perform sanity check of all messages and
    the members that can be verified:
    - validate sequence, length and that the subfunction (sa_type) is supported,
      i.e. the service 0x27 properties.
    - verify auth_data
    - verify content of members, including message_id, authentication_method (e.g. message_id
      is 0x0001 for the client_request_seed message, authentication_method is 0x0001, etc.)
    - encrypted data records, must only be processed once auth_data verification is
      passed, to verify server- and client proof of ownership respectively (when encrypted data
    records have been decrypted).

    Upon any failure, the message shall be rejected.

details: >
    Validate message structure of security access subfunctions- clientRequestSeed,
    serverResponseSeed, clientSendKey and serverResponseKey.
    Steps-
    1. Validate clientRequestSeed - validate length, sequence and message data
    2. Validate serverResponseSeed - validate length, sequence and message data
    3. Validate clientSendKey - validate length, sequence and message data
    4. Validate serverResponseKey - validate length, sequence and message data
"""

import time
import copy
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_file_io import SupportFileIO

SSA = SupportSecurityAccess()
SIO = SupportFileIO()


def extract_client_request_seed(message, parameters):
    """
    Extract the respective data bytes from the security access client request seed message
    Args:
        message (str): Response of client request seed
        parameters (dict): Security access levels
    Returns:
        client_seed_dict (dict): Client request seed message structure
    """
    client_seed_dict = {'sa_sid': '',
                        'sa_type': '',
                        'message_id': '',
                        'authentication': '',
                        'iv': '',
                        'encrypt_data_record': '',
                        'auth_data': ''}

    if len(message) == parameters['response_length']['client_req_sid_len']:
        client_seed_dict['sa_sid'] = message[:parameters['message_pos_len']['type_pos']]

        client_seed_dict['sa_type'] = message[parameters['message_pos_len']['type_pos']:
                                              parameters['message_pos_len']['msg_id_pos']]

        client_seed_dict['message_id'] = message[parameters['message_pos_len']['msg_id_pos']:
                                                 parameters['message_pos_len']['auth_method_pos']]

        client_seed_dict['authentication'] = \
            message[parameters['message_pos_len']['auth_method_pos']:
                    parameters['message_pos_len']['req_seed_iv_pos']]

        client_seed_dict['iv'] = message[parameters['message_pos_len']['req_seed_iv_pos']:
                                         parameters['message_pos_len']['req_seed_encrypt_pos']]

        client_seed_dict['encrypt_data_record'] = \
            message[parameters['message_pos_len']['req_seed_encrypt_pos']:
                    parameters['message_pos_len']['req_seed_auth_data_pos']]

        client_seed_dict['auth_data'] = message[parameters['message_pos_len']
                                                ['req_seed_auth_data_pos']:]
    else:
        logging.error("Failed to store client request seed data in dictionary")

    return client_seed_dict


def extract_server_response_seed(message, parameters):
    """
    Extract the respective data bytes from the security access server response seed message
    Args:
        message (str): Response of server response seed
        parameters (dict): Security access levels
    Returns:
        server_response_dict (dict): Server response seed message structure
    """
    server_response_dict = {'sa_sid': '',
                            'sa_type': '',
                            'message_id': '',
                            'iv': '',
                            'encrypt_data_record': '',
                            'auth_data': ''}

    if len(message) == parameters['response_length']['server_res_sid_len']:
        server_response_dict['sa_sid'] = message[: parameters['message_pos_len']['type_pos']]

        server_response_dict['sa_type'] = message[parameters['message_pos_len']['type_pos']:
                                                  parameters['message_pos_len']['msg_id_pos']]

        server_response_dict['message_id'] = message[parameters['message_pos_len']['msg_id_pos']:
                                                parameters['message_pos_len']['res_seed_iv_pos']]

        server_response_dict['iv'] = message[parameters['message_pos_len']['res_seed_iv_pos']:
                                             parameters['message_pos_len']['res_seed_encrypt_pos']]

        server_response_dict['encrypt_data_record'] = \
            message[parameters['message_pos_len']['res_seed_encrypt_pos']:
                    parameters['message_pos_len']['res_seed_auth_data_pos']]

        server_response_dict['auth_data'] = message[parameters['message_pos_len']
                                                    ['res_seed_auth_data_pos']:]
    else:
        logging.error("Failed to store server response seed data in dictionary")

    return server_response_dict


def extract_client_send_key(message, parameters):
    """
    Extract the respective data bytes from the security access client send key message
    Args:
        message (str): Response of client send key
        parameters (dict): Security access levels
    Returns:
        client_send_key_dict (dict): Client send key message structure
    """
    client_send_key_dict = {'sa_sid': '',
                            'sa_type': '',
                            'message_id': '',
                            'iv': '',
                            'encrypt_data_record': '',
                            'auth_data': ''}

    if len(message) == parameters['response_length']['client_sent_key_len']:
        client_send_key_dict['sa_sid'] = message[:parameters['message_pos_len']['type_pos']]

        client_send_key_dict['sa_type'] = message[parameters['message_pos_len']['type_pos']:
                                                  parameters['message_pos_len']['msg_id_pos']]

        client_send_key_dict['message_id'] = message[parameters['message_pos_len']['msg_id_pos']:
                                                 parameters['message_pos_len']['req_key_iv_pos']]

        client_send_key_dict['iv'] = message[parameters['message_pos_len']['req_key_iv_pos']:
                                             parameters['message_pos_len']['req_key_encrypt_pos']]

        client_send_key_dict['encrypt_data_record'] = \
                                   message[parameters['message_pos_len']['req_key_encrypt_pos']:
                                        parameters['message_pos_len']['req_key_auth_data_pos']]

        client_send_key_dict['auth_data'] = message[parameters['message_pos_len']
                                                    ['req_key_auth_data_pos']:]
    else:
        logging.error("Failed to store client send key data in dictionary")

    return client_send_key_dict


def extract_server_response_key(message, parameters):
    """
    Extract the respective data bytes from the security access server response key message
    Args:
        message (str): Response of server response key
        parameters (dict): Security access levels
    Returns:
        server_res_key_dict (dict): Server response key message structure
    """
    server_res_key_dict = {'sa_response_sid': '',
                           'sa_type': ''}

    if len(message) == parameters['response_length']['server_res_key_len']:
        server_res_key_dict['sa_response_sid'] = message[:parameters['message_pos_len']
                                                                          ['type_pos']]

        server_res_key_dict['sa_type'] = message[parameters['message_pos_len']['type_pos']:
                                               parameters['message_pos_len']['msg_id_pos']]
    else:
        logging.error("Failed to store server response key data in dictionary")

    return server_res_key_dict


def security_access_method(dut: Dut):
    """
    Request for security access to ECU and store response of all sub functions
    Args:
        dut (Dut): An instance of dut
    Returns:
        payload_dict (dict): Security access response of all sub functions
    """
    payload_dict = {'client_seed': '',
                    'server_seed': '',
                    'client_key': '',
                    'server_key': ''}

    # Set to programming session
    dut.uds.set_mode(2)

    #timer to avoid NRC 37
    time.sleep(5)

    # Set security access key
    SSA.set_keys(dut.conf.default_rig_config)
    SSA.set_level_key(1)

    # Prepare request for a 'client request seed'
    client_req_seed = SSA.prepare_client_request_seed()
    payload_dict['client_seed'] = client_req_seed

    if payload_dict['client_seed'] is None:
        logging.error("Empty security access response for clientRequestSeed")
    response = dut.uds.generic_ecu_call(client_req_seed)

    # Prepare server seed payload by truncating first 2 bytes of message
    payload_dict['server_seed'] = response.raw[4:]

    if payload_dict['server_seed'] is None:
        logging.error("Empty security access response for ServerResponseSeed")

    result = SSA.process_server_response_seed(
        bytearray.fromhex(payload_dict['server_seed']))

    client_send_key = SSA.prepare_client_send_key()
    payload_dict['client_key'] = client_send_key.hex().upper()

    if payload_dict['client_key'] is None:
        logging.error("Empty security access response for clientSendKey")
    response = dut.uds.generic_ecu_call(client_send_key)

    # Prepare response from  6th byte to 6+4 bytes for server response key
    result = SSA.process_server_response_key(
        bytearray.fromhex(response.raw[6:(6+4)]))

    # Prepare server key payload from 2nd to 6th byte of message for response id and SA type
    payload_dict['server_key'] = response.raw[2:6]

    if payload_dict['server_key'] is None:
        logging.error("Empty security access response for serverResponseKey")

    if result != 0:
        logging.error("Security access to ECU not successful")
        return None

    return payload_dict


def verify_sa_message(sa_dict, parameters, message_type):
    """
    Verify length and content of security access message structure members
    Args:
        sa_dict (dict): Security access message response
        parameters (dict): Security access levels
        message_type (str): Security access message structure type
    Returns:
        (bool): True when successfully verified length and content of security access message
                      structure members
    """
    results = []

    # verify message length and content of SA id, SA type, message_id messages
    if len(sa_dict['sa_sid']) == len(parameters[message_type]['sa_sid']) and \
            sa_dict['sa_sid'] == parameters[message_type]['sa_sid']:
        results.append(True)
    else:
        logging.error("%s - sa_sid length or data does not match", message_type)
        results.append(False)

    if len(sa_dict['sa_type']) == len(parameters[message_type]['sa_type']) and \
            sa_dict['sa_type'] == parameters[message_type]['sa_type']:
        results.append(True)
    else:
        logging.error("%s - sa_type length or data does not match", message_type)
        results.append(False)

    if len(sa_dict['message_id']) == len(parameters[message_type]['message_id']) and \
            sa_dict['message_id'] == parameters[message_type]['message_id']:
        results.append(True)
    else:
        logging.error("%s - message_id length or data does not match", message_type)
        results.append(False)

    # Verify message length of iv(initialization vector), encrypt data record and
    # authentication data messages
    if len(sa_dict['encrypt_data_record']) == parameters[message_type]['encrypt_data_rec_len']\
            and len(sa_dict['iv']) == parameters[message_type]['iv_len']:
        results.append(True)
    else:
        logging.error("%s - encrypt data record or iv length does not match", message_type)
        results.append(False)

    if len(sa_dict['auth_data']) == parameters[message_type]['auth_data_len']:
        results.append(True)
    else:
        logging.error("%s - authentication data length does not match", message_type)
        results.append(False)

    if not all(results) and len(results) != 0:
        return False

    return True


def step_1(dut: Dut):
    """
    action: Request for security access to ECU.
    expected_result: Empty security access response should not be sent for all sub-functions.
    """
    # Sleep time to avoid NRC37
    time.sleep(5)
    payload_dict = security_access_method(dut)
    if payload_dict is not None:
        logging.info("Received valid security access response for all sub-functions as expected")
        return True, payload_dict

    logging.error("Test Failed: Received empty security access response for all sub-functions %s",
                  payload_dict)
    return False, None


def step_2(dut: Dut, payload_dict, parameters):
    """
    action: Verify length and content of authentication method message and client request seed
            message structure
    expected_result: Content of authentication method message should be equal to client seed
                     request auth method and structure of client request seed message should be
                     valid
    """
    # pylint: disable=unused-argument
    result = False
    client_seed_dict = extract_client_request_seed(payload_dict['client_seed'].hex(), parameters)
    result = verify_sa_message(client_seed_dict, parameters, 'client_seed_request')

    # Verify message length and content of authentication method message
    if len(client_seed_dict['authentication']) == \
        len(parameters['client_seed_request']['auth_method'])\
        and client_seed_dict['authentication'] == parameters['client_seed_request']['auth_method']:
        auth_result = True
    else:
        logging.error("Test Failed: client_seed_request - authentication id length does not match")
        auth_result = False

    if result and auth_result:
        logging.info("Received valid client request seed message structure as expected")
        return True

    logging.error("Test Failed: Received invalid client request seed message structure %s",
                  client_seed_dict)
    return False


def step_3(dut: Dut, payload_dict, parameters):
    """
    action: Verify server response seed message structure
    expected_result: Structure of server response seed message should be valid
    """
    # pylint: disable=unused-argument
    result = False
    server_response_dict = extract_server_response_seed(payload_dict['server_seed'], parameters)
    result = verify_sa_message(server_response_dict, parameters, 'server_seed_response')
    if result:
        logging.info("Received valid server response seed message structure as expected")
        return True

    logging.error("Test Failed: Received invalid server response seed message structure %s",
                  server_response_dict)
    return False


def step_4(dut: Dut, payload_dict, parameters):
    """
    action: Verify client send key message structure
    expected_result: Structure of client send key message should be valid
    """
    # pylint: disable=unused-argument
    result = False
    client_send_key_dict = extract_client_send_key(payload_dict['client_key'], parameters)
    result = verify_sa_message(client_send_key_dict, parameters, 'client_send_key')
    if result:
        logging.info("Received valid client send key message structure as expected")
        return True

    logging.error("Test Failed: Received invalid client send key message structure %s",
                  client_send_key_dict)
    return False


def step_5(dut: Dut, payload_dict, parameters):
    """
    action: Verify server response key message structure
    expected_result: Structure of server response key message should be valid and security access
                     type length or data should match
    """
    # pylint: disable=unused-argument
    result = []
    server_res_key_dict = extract_server_response_key(payload_dict['server_key'], parameters)

    # comparing server_response key payload value with yml parameters
    # and verify message length and content
    if len(server_res_key_dict['sa_response_sid']) == \
        len(parameters['server_response_key']['response_sid']) and \
        server_res_key_dict['sa_response_sid'] == \
        parameters['server_response_key']['response_sid']:
        result.append(True)
    else:
        logging.error("Invalid server response key - security access service id data or "
                      "length does not match")
        result.append(False)

    if len(server_res_key_dict['sa_type']) == \
        len(parameters['server_response_key']['sa_type']) and \
        server_res_key_dict['sa_type'] == parameters['server_response_key']['sa_type']:
        result.append(True)
    else:
        logging.error("Test Failed: Invalid server response key - security access type length or "
                      "data does not match")
        result.append(False)

    if all(result):
        logging.info("Received valid server response key message structure as expected")
        return True

    logging.error("Test Failed: Receive invalid server response key message structure %s",
                  server_res_key_dict)
    return False


def step_6(dut: Dut, payload_dict):
    """
    action: Verify negative response for invalid client request seed message
    expected_result: ECU should send NRC-12(subFunctionNotSupported) for invalid client request
                     seed message
    """
    payload = copy.deepcopy(payload_dict['client_seed'])

    # Corrupt request seed sub-function and validate NRC response
    payload[1] = 0x00
    response = dut.uds.generic_ecu_call(payload)

    # Check NRC-12(subFunctionNotSupported) for corrupted client seed
    if response.raw[6:8] == '12':
        logging.info("Received NRC-12(subFunctionNotSupported) for invalid client request "
                     "seed message as expected")
        return True

    logging.error("Test Failed: Expected NRC-12(subFunctionNotSupported) for invalid client "
                  "request seed message, received %s", response.raw[6:8])
    return False


def step_7(dut: Dut, payload_dict):
    """
    action: Verify negative response for invalid client request seed message
    expected_result: ECU should send NRC-31(requestOutOfRange) for invalid client request seed
                     message
    """
    payload = copy.deepcopy(payload_dict['client_seed'])
    # Modify request seed message id and validate NRC-31(requestOutOfRange) response
    payload[2] = 0x01
    response = dut.uds.generic_ecu_call(payload)

    # Check NRC-31(requestOutOfRange) for corrupted client seed
    if response.raw[6:8] == '31':
        logging.info("Received NRC-31(requestOutOfRange) for invalid client request "
                     "seed as expected")
        return True

    logging.error("Test Failed: Expected NRC-31(requestOutOfRange) for invalid client "
                  "request seed message, received %s", response.raw[6:8])
    return False


def step_8(dut: Dut, payload_dict):
    """
    action: Verify negative response for invalid client request seed message- authentication id
    expected_result: ECU should send NRC-31(requestOutOfRange) for invalid client request seed
                     message- authentication id
    """
    payload = copy.deepcopy(payload_dict['client_seed'])

    # Modify request seed authentication id and validate NRC-31 response
    payload[4] = 0x01
    response = dut.uds.generic_ecu_call(payload)

    # Check NRC 31(requestOutOfRange) for corrupted client seed
    if response.raw[6:8] == '31':
        logging.info("Received NRC-31(requestOutOfRange) for invalid client request seed "
                     "as expected")
        return True

    logging.error("Test Failed: Expected NRC-31(requestOutOfRange) for invalid client "
                  "request seed message, received %s", response.raw[6:8])
    return False


def run():
    """
    Validate message structure of security access for subfunctions - clientRequestSeed,
    serverResponseSeed, clientSendKey and serverResponseKey. verify Negative response on failure.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'client_seed_request': {},
                       'server_seed_response': {},
                       'client_send_key': {},
                       'server_response_key': {},
                       'response_length': {},
                       'message_pos_len': {}}
    try:
        dut.precondition(timeout=30)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step, payload_dict = dut.step(step_1, purpose="Security access to ECU")
        if result_step:
            result_step = dut.step(step_2, payload_dict, parameters,
                                   purpose="Check clientRequestSeed - message structure")
        if result_step:
            result_step = dut.step(step_3, payload_dict, parameters,
                                   purpose="Check serverResponseSeed - message structure")
        if result_step:
            result_step = dut.step(step_4, payload_dict, parameters,
                                   purpose="Check clientSendKey - message structure")
        if result_step:
            result_step = dut.step(step_5, payload_dict, parameters,
                                   purpose="Check serverResponseKey - message structure")
        if result_step:
            result_step = dut.step(step_6, payload_dict,
                                   purpose="Check response for invalid subfunction")
        if result_step:
            result_step = dut.step(step_7, payload_dict,
                                  purpose="Check response for invalid message id")
        if result_step:
            result_step = dut.step(step_8, payload_dict,
                                   purpose="Check response for invalid authentication id")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
