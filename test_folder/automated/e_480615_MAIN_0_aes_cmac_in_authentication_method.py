"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 480615
version: 0
title: >
    AES-CMAC in authentication method 0x0001

purpose: >
    Define algorithm for authentication method 0x0001, to generate/verify
    message authentication codes and proof of ownerships.

description: >
    The AES-CMAC MAC algorithm for authentication_method 0x0001 shall be according to CMAC mode for
    authentication, as defined in NIST Special Publication 800-38B. The underlying block cipher
    shall be Advanced Encryption Standard (AES) (FIPS 197), where the key length is 128 bits
    (AES-128-CMAC).
    This algorithm is used to calculate message authentication_data, client_proof_of_ownership,
    and server_proof_of_ownership.

details: >
    Verify message authentication code, server and client proof of ownership in both
    programming and extended session
        1. Security access to ECU and get subfunctions responses
        2. Calculate CMAC of client request seed, server response seed and client
           send key using AES-CMAC algorithm and verify
        3. Decrypt encrypted data using AES-CTR and verify client and server proof of ownership
"""

import logging
import time
from Crypto.Util import Counter
from Crypto.Hash import CMAC
from Crypto.Cipher import AES
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_file_io import SupportFileIO

SSA = SupportSecurityAccess()
SIO = SupportFileIO()


def security_access(dut: Dut, sa_level):
    """
    Security access to ECU and get subfunctions response
    Args:
        dut (Dut): An instance of Dut
        sa_level (int): Security access level
    Returns:
        sa_response_dict (dict): Security access subfunctions request and response message
    """
    sa_response_dict = {'client_req_seed': '',
                        'server_res_seed': '',
                        'client_send_key': ''
                        }
    SSA.set_keys(dut.conf.default_rig_config)
    SSA.set_level_key(sa_level)
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
        logging.error("Security access not successful")
        return None

    return sa_response_dict


def calculate_authentication_data(dut: Dut, message):
    """
    Calculate message authentication data using Crypto AES-128-CMAC algorithm
    Args:
        dut (Dut): An instance of Dut
        message (str): Security access message
    Returns:
        calculated_cmac (str): Calculated authentication data
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
        dut (Dut): An instance of Dut
        random_number1 (str): Random number 1
        random_number2 (str): Random number 2
    Returns:
        calculated_cmac (str): Calculated proof of ownership
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
        dut (Dut): An instance of Dut
        init_vector (str): Initialization vector
        encrypted_data (str): Encrypted data record
    Returns:
        decrypted_data (str): Decrypted data record
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
        dut (Dut): An instance of Dut
        req_seed_message (str): Client request seed message
        position (dict): Positions of IV and random number
    Returns:
        client_random_number (str): Decrypted client random number
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
        dut (Dut): An instance of Dut
        req_seed_message (str): Server response seed message
        position(dict): Positions of IV and random number
    Returns:
        dec_server_data (str): Decrypted server data
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
        dut (Dut): An instance of Dut
        send_key (str): Client send key message
        position (dict): Positions of IV and random number
    Returns:
        client_ownership (str): Decrypted client proof of ownership
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
    action: Set to programming session, security access to ECU and get subfunctions response
    expected_result: Should get security access messages of all subfunctions when ECU unlocked
    """
    # Set to programming session
    dut.uds.set_mode(2)

    # Sleep time to avoid NRC37
    time.sleep(5)

    sa_response_dict = security_access(dut, sa_level=1)
    if sa_response_dict is None:
        logging.error("Test Failed: Security access not successful")
        return False, None

    return True, sa_response_dict


def step_2(dut: Dut, req_seed_msg, req_seed_pos):
    """
    action: Calculate and verify client request seed CMAC in programming session
    expected_result: Client request seed CMAC should be successfully verified
    """
    calculated_cmac = calculate_authentication_data(dut, req_seed_msg[:req_seed_pos['rand_end']])
    req_seed_cmac = req_seed_msg[req_seed_pos['cmac_start']:]
    if calculated_cmac == req_seed_cmac:
        logging.info("Client request seed CMAC verification successful")
        return True

    logging.error("Test Failed: Client request seed CMAC verification failed expected %s, "
                  "calculated CMAC %s", req_seed_cmac, calculated_cmac)
    return False


def step_3(dut: Dut, res_seed_msg, res_seed_pos):
    """
    action: Calculate and verify server response seed CMAC in programming session
    expected_result: Server response seed CMAC should be successfully verified
    """
    calculated_cmac = calculate_authentication_data(dut,
                                                    res_seed_msg[:res_seed_pos['ownership_end']])
    res_seed_cmac = res_seed_msg[res_seed_pos['cmac_start']:]

    if calculated_cmac == res_seed_cmac:
        logging.info("Server response seed CMAC verification successful")
        return True

    logging.error("Test Failed: Server response seed CMAC verification failed expected %s, "
                  "calculated CMAC %s", res_seed_cmac, calculated_cmac)
    return False


def step_4(dut: Dut, send_key_msg, send_key_pos):
    """
    action: Calculate and verify client send key CMAC in programming session
    expected_result: Client send key CMAC should be successfully verified
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


def step_5(dut: Dut, sa_message, parameters):
    """
    action: Calculate and verify server proof of ownership in programming session
    expected_result: Server proof of ownership should be successfully verified
    """
    client_random_number = get_client_random_number(dut, sa_message['client_req_seed'],
                                                    parameters['client_seed_pos'])

    dec_server_data = get_server_decrypted_data(dut, sa_message['server_res_seed'],
                                                parameters['server_seed_pos'])
    server_random_number = dec_server_data[:32]
    ecu_server_ownership = dec_server_data[32:]

    calculated_server_ownership = calculate_ownership_proof(dut,
                                                            server_random_number,
                                                            client_random_number)
    if ecu_server_ownership == calculated_server_ownership:
        logging.info("Server proof of ownership verified successfully")
        return True

    logging.error("Test Failed: Server proof of ownership failed expected %s, received %s",
                  ecu_server_ownership, calculated_server_ownership)
    return False


def step_6(dut: Dut, sa_message, parameters):
    """
    action: Calculate and verify client proof of ownership in programming session
    expected_result: Client proof of ownership should be successfully verified
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


def step_7(dut: Dut):
    """
    action: Set to extended session, security access to ECU and get subfunctions response
    expected_result: Should get security access messages of all subfunctions when ECU unlocked
    """
    # Set to extended session
    dut.uds.set_mode(1)
    dut.uds.set_mode(3)

    # Adding a sleep timer to avoid NRC 37 (requiredTimeDelayNotExpired)
    time.sleep(5)

    sa_response_dict = security_access(dut, sa_level=5)
    if sa_response_dict is None:
        logging.error("Test Failed: Security access not successful")
        return False, None

    return True, sa_response_dict


def step_8(dut: Dut, req_seed_msg, req_seed_pos):
    """
    action: Calculate and verify client request seed CMAC in extended session
    expected_result: Client request seed CMAC should be successfully verified
    """
    calculated_cmac = calculate_authentication_data(dut, req_seed_msg[:req_seed_pos['rand_end']])
    req_seed_cmac = req_seed_msg[req_seed_pos['cmac_start']:]

    if calculated_cmac == req_seed_cmac:
        logging.info("Client request seed CMAC verification successful")
        return True

    logging.error("Test Failed: Client request seed CMAC verification failed expected %s, "
                  "calculated CMAC %s", req_seed_cmac, calculated_cmac)
    return False


def step_9(dut: Dut, res_seed_msg, res_seed_pos):
    """
    action: Calculate and verify server response seed CMAC in extended session
    expected_result: Server response seed CMAC should be successfully verified
    """
    calculated_cmac = calculate_authentication_data(dut,
                                                    res_seed_msg[:res_seed_pos['ownership_end']])
    res_seed_cmac = res_seed_msg[res_seed_pos['cmac_start']:]

    if calculated_cmac == res_seed_cmac:
        logging.info("Server response seed CMAC verification successful")
        return True

    logging.error("Test Failed: Server response seed CMAC verification failed expected %s, "
                  "calculated CMAC %s", res_seed_cmac, calculated_cmac)
    return False


def step_10(dut: Dut, send_key_msg, send_key_pos):
    """
    action: Calculate and verify client send key CMAC in extended session
    expected_result: Client send key CMAC should be successfully verified
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


def step_11(dut: Dut, sa_message, parameters):
    """
    action: Calculate and verify server proof of ownership in extended session
    expected_result: Server proof of ownership should be successfully verified
    """
    client_random_number = get_client_random_number(dut, sa_message['client_req_seed'],
                                                    parameters['client_seed_pos'])

    dec_server_data = get_server_decrypted_data(dut, sa_message['server_res_seed'],
                                                parameters['server_seed_pos'])
    server_random_number = dec_server_data[:32]

    ecu_server_ownership = dec_server_data[32:]
    calculated_server_ownership = calculate_ownership_proof(dut,
                                                            server_random_number,
                                                            client_random_number)

    if ecu_server_ownership == calculated_server_ownership:
        logging.info("Server proof of ownership verified successfully")
        return True

    logging.error("Test Failed: Server proof of ownership failed expected %s, received %s",
                  ecu_server_ownership, calculated_server_ownership)
    return False


def step_12(dut: Dut, sa_message, parameters):
    """
    action: Calculate and verify client proof of ownership in extended session
    expected_result: Client proof of ownership should be successfully verified
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
    Security access method verification in programming and extended session
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'client_seed_pos': {},
                       'server_seed_pos': {},
                       'client_key_pos': {}}
    try:
        dut.precondition(timeout=60)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameter not found")

        result_step, sa_message = dut.step(step_1, purpose="Security access to ECU in programming "
                                  "session and get all subfunction request & response message")

        result_step = result_step and dut.step(step_2, sa_message['client_req_seed'],
                      parameters['client_seed_pos'], purpose="Verify client request seed CMAC ")

        result_step = result_step and dut.step(step_3, sa_message['server_res_seed'],
                      parameters['server_seed_pos'], purpose="Verify server response seed CMAC")

        result_step = result_step and dut.step(step_4, sa_message['client_send_key'],
                      parameters['client_key_pos'], purpose="Verify client send key CMAC")

        result_step = result_step and dut.step(step_5, sa_message, parameters,
                      purpose="Verify server proof of ownership")

        result_step = result_step and dut.step(step_6, sa_message, parameters,
                      purpose="Verify client proof of ownership")

        result_step, sa_message_e = result_step and dut.step(step_7, purpose="Security access "
                                    "to ECU in extended session and get all subfunction request "
                                    " & response message")

        result_step = result_step and dut.step(step_8, sa_message_e['client_req_seed'],
                      parameters['client_seed_pos'],  purpose="Verify client request seed CMAC")

        result_step = result_step and dut.step(step_9, sa_message_e['server_res_seed'],
                      parameters['server_seed_pos'], purpose="Verify server response seed CMAC")

        result_step = result_step and dut.step(step_10, sa_message_e['client_send_key'],
                      parameters['client_key_pos'], purpose="Verify client send key CMAC")

        result_step = result_step and dut.step(step_11, sa_message_e, parameters,
                      purpose="Verify server proof of ownership")

        result_step = result_step and dut.step(step_12, sa_message_e, parameters,
                      purpose="Verify client proof of ownership")

        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
