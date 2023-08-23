"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 480623
version: 0
title: clientSendKey - construction
purpose: >
    To define the clientSendKey content for authentication_method = 0x0001.

description: >
    The following shall be applied when constructing the clientSendKey message:
    encrypted_data_record:
    This shall be the AES-128-CTR encryption output, calculated using the IV as initialization
    vector and the client_proof_of_ownership as plaintext input.

    client_proof_of_ownership shall be the client response to the server random number, by
    generating an AES-128-CMAC output using the concatenation of following inputs and order:
    client_random_number
    server_random_number

    authentication_data:
    This shall be the AES-128-CMAC output be calculated using following inputs:
    security_access_request_sid
    security_access_type
    message_id
    iv
    encrypted_data_record

    Example 1:
    Generation of the client_proof_of_ownership, i.e. the AES-128-CMAC output of the concatenation
    of client_random_number and server_random_number. Note that the input order of random numbers
    is not equal to the order used to calculate the server_proof_of_ownership.

details: >
    Verify message authentication code and client proof of ownership
    1. Security access to ECU and get subfunctions responses
    2. Calculate CMAC of client send key using AES-128-CMAC algorithm and verify
    3. Decrypt encrypted data using AES-CTR and verify client proof of ownership
"""

import time
import logging
from Crypto.Util import Counter
from Crypto.Hash import CMAC
from Crypto.Cipher import AES
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_file_io import SupportFileIO

SSA = SupportSecurityAccess()
SIO = SupportFileIO()


def security_access(dut: Dut):
    """
    Security access to ECU and get subfunctions response
    Args:
        dut(Dut): An instance of Dut
    Returns:
        sa_response_dict(dict): Security access subfunctions request and response message
    """
    sa_response_dict = {'client_req_seed': '',
                        'server_res_seed': '',
                        'client_send_key': ''
                        }
    SSA.set_keys(dut.conf.default_rig_config)
    SSA.set_level_key(1)
    payload = SSA.prepare_client_request_seed()
    sa_response_dict['client_req_seed'] = payload.hex().upper()

    response = dut.uds.generic_ecu_call(payload)
    # Prepare server response seed
    server_res_seed = response.raw[4:]
    result = SSA.process_server_response_seed(bytearray.fromhex(server_res_seed))
    sa_response_dict['server_res_seed'] = server_res_seed

    payload = SSA.prepare_client_send_key()
    sa_response_dict['client_send_key'] = payload.hex().upper()

    response = dut.uds.generic_ecu_call(payload)

    # Process server response key
    result = SSA.process_server_response_key(bytearray.fromhex(response.raw[6:(6+4)]))
    if result != 0:
        logging.error("Security Access not successful")
        return None
    return sa_response_dict


def calculate_authentication_data(dut: Dut, message):
    """
    Calculate message authentication data using Crypto AES-128-CMAC algorithm
    Args:
        dut(Dut): An instance of Dut
        message(str): security access message
    Returns:
        calculated_cmac(Str): Calculated authentication data
    """
    # Get 128 bits auth_key from config
    key_128 = bytes.fromhex(dut.conf.default_rig_config['auth_key'])
    cipher_obj = CMAC.new(key_128, ciphermod=AES)
    cipher_obj.update(bytes.fromhex(message))
    calculated_cmac = cipher_obj.hexdigest().upper()

    return calculated_cmac


def calculate_ownership_proof(dut: Dut, random_number1, random_number2):
    """
    Calculate message authentication data using Crypto AES-128-CMAC algorithm
    Args:
        dut(Dut): An instance of Dut
        random_number1(str): random number1
        random_number2(str): random number2
    Returns:
        calculated_cmac(Str): Calculated proof of ownership
    """
    # Get 128 bits proof_key from config
    key_128 = bytes.fromhex(dut.conf.default_rig_config['proof_key'])
    cipher_obj = CMAC.new(key_128, ciphermod=AES)
    cipher_obj.update(bytes.fromhex(random_number1+random_number2))
    ownership_proof = cipher_obj.hexdigest().upper()

    return ownership_proof


def decrypt_data(dut: Dut, init_vector, encrypted_data):
    """
    Decrypt encrypted data using Crypto AES-CTR algorithm
    Args:
        dut(Dut): An instance of Dut
        init_vector(str): initialization vector
        encrypted_data(str): Encrypted data record
    Returns:
        decrypted_data(Str): Decrypted data record
    """
    # Get 128 bits auth_key from config
    key_128 = bytes.fromhex(dut.conf.default_rig_config['auth_key'])
    counter = Counter.new(128,
                          initial_value=int.from_bytes(bytes.fromhex(init_vector),
                          byteorder='big'), little_endian=False)
    cipher_dec_obj = AES.new(key_128, AES.MODE_CTR, counter=counter)
    decrypted_data = cipher_dec_obj.decrypt(bytes.fromhex(encrypted_data))
    return decrypted_data.hex().upper()


def get_client_random_number(dut: Dut, req_seed_message, position):
    """
    Decrypt client random number
    Args:
        dut(Dut): An instance of Dut
        req_seed_message(str): client request seed message
        position(dict): positions of IV and random number
    Returns:
        client_random_number(Str): Decrypted client random number
    """
    iv_start_pos = position['iv_start']
    iv_end_pos = position['iv_end']
    req_seed_iv = req_seed_message[iv_start_pos:iv_end_pos]

    start_pos = position['rand_start']
    end_pos = position['rand_end']
    enc_client_rand_number = req_seed_message[start_pos:end_pos]
    client_random_number = decrypt_data(dut, req_seed_iv, enc_client_rand_number)

    return client_random_number


def get_server_decrypted_data(dut: Dut, res_seed_message, position):
    """
    Decrypt server response seed data record
    Args:
        dut(Dut): An instance of Dut
        req_seed_message(str): server response seed message
        position(dict): positions of IV and random number
    Returns:
        dec_server_data(Str): Decrypted server data
    """
    iv_start_pos = position['iv_start']
    iv_end_pos = position['iv_end']
    res_seed_iv = res_seed_message[iv_start_pos:iv_end_pos]

    start_pos = position['rand_start']
    end_pos = position['ownership_end']
    enc_server_data = res_seed_message[start_pos:end_pos]
    dec_server_data = decrypt_data(dut, res_seed_iv, enc_server_data)

    return dec_server_data


def get_client_proof_of_ownership(dut: Dut, send_key, position):
    """
    Decrypt client random number to get client proof of ownership
    Args:
        dut(Dut): An instance of Dut
        send_key(str): client send key message
        position(dict): positions of IV and random number
    Returns:
        client_ownership(str): Decrypted client proof of ownership
    """
    iv_start_pos = position['rand_start']
    iv_end_pos = position['rand_end']
    send_key_iv = send_key[iv_start_pos:iv_end_pos]

    start_pos = position['ownership_start']
    end_pos = position['ownership_end']
    enc_client_proof_of_ownership = send_key[start_pos:end_pos]
    client_ownership = decrypt_data(dut, send_key_iv, enc_client_proof_of_ownership)

    return client_ownership


def step_1(dut: Dut):
    """
    action: Set to programming session, security access to ECU and get subfunctions response.
    expected_result: True with security access messages of all subfunctions when ECU unlocked
    """
    #Sleep time to avoid NRC37
    time.sleep(5)

    dut.uds.set_mode(2)
    sa_response_dict = security_access(dut)
    if sa_response_dict is None:
        logging.error("Test Failed: Security access not successful")
        return False, None
    return True, sa_response_dict


def step_2(dut: Dut, send_key_msg, send_key_pos):
    """
    action: Calculate and verify client send key CMAC
    expected_result: True on successfully verified client send key CMAC
    """
    calculated_cmac = calculate_authentication_data(dut,
                                                    send_key_msg[:send_key_pos['ownership_end']])
    send_key_cmac = send_key_msg[send_key_pos['cmac_start']:]
    if calculated_cmac == send_key_cmac:
        logging.info("Client send key CMAC verification successful")
        return True
    logging.error("Test Failed: Client send key CMAC verification failed expected %s, "
                  "calculated CMAC %s", send_key_cmac, calculated_cmac)
    return False


def step_3(dut: Dut, sa_message, parameters):
    """
    action: Calculate and verify client proof of ownership
    expected_result: True on successfully verified client proof of ownership
    """
    client_random_number = get_client_random_number(dut, sa_message['client_req_seed'],
                                                    parameters['client_seed_pos'])

    dec_server_data = get_server_decrypted_data(dut, sa_message['server_res_seed'],
                                                parameters['server_seed_pos'])
    server_random_number = dec_server_data[:32]

    ecu_client_ownership = get_client_proof_of_ownership(dut, sa_message['client_send_key'],
                                                         parameters['client_key_pos'])
    calculated_client_ownership = calculate_ownership_proof(dut,
                                                            client_random_number,
                                                            server_random_number)

    if ecu_client_ownership == calculated_client_ownership:
        logging.info("Client proof of ownership verified successfully")
        return True
    logging.error("Test Failed: Client proof of ownership failed expected %s, received %s",
                  ecu_client_ownership, calculated_client_ownership)
    return False


def run():
    """
    Verify message authentication code and client proof of ownership
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False
    parameters_dict = {'client_seed_pos': {},
                       'server_seed_pos': {},
                       'client_key_pos': {}
                       }
    try:
        dut.precondition(timeout=60)
        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameter not found")

        result_step, sa_message = dut.step(step_1, purpose="Security access to ECU and get "
                                           "all subfunction request & response message")
        if result_step:
            result_step = dut.step(step_2, sa_message['client_send_key'],
                                   parameters['client_key_pos'],
                                   purpose="Verify client send key CMAC")
        if result_step:
            result_step = dut.step(step_3, sa_message, parameters,
                                   purpose="Verify client proof of ownership")

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
