"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 480620
version: 0
title: clientRequestSeed - construction
purpose: >
    To define the clientRequestSeed  content for authentication_method = 0x0001.

description: >
    The following shall be applied when constructing the clientRequestSeed message:
    encrypted_data_record
    This shall be the AES-128-CTR encryption output, calculated using the IV as the algorithm
    initialization vector and the client_random_number as plaintext input.

    authentication_data
    This shall be the AES-128-CMAC output calculated using following inputs and order according
    to the request message structure:
    security_access_request_sid
    security_access_type
    message_id
    authentication_method
    iv
    encrypted_data_record

details: >
    Calculate authentication data using Crypto AES-128-CMAC algorithm and verify with
    clientRequestSeed authentication data.
    Steps-
        1. Security access to ECU and get the client request seed message
        2. Calculate authentication data using AES-128-CMAC and verify
"""

import time
import logging
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
    Get client request and response seed message
    Args:
        dut (Dut): An instance of Dut
    Returns:
        sa_response_dict (dict): Security access client request and response seed message
    """
    sa_response_dict = {'client_req_seed': '',
                        'server_res_seed': ''}

    SSA.set_keys(dut.conf.default_rig_config)
    SSA.set_level_key(1)
    payload = SSA.prepare_client_request_seed()
    sa_response_dict['client_req_seed'] = payload.hex().upper()

    response = dut.uds.generic_ecu_call(payload)
    # Prepare server response seed
    server_res_seed = response.raw[4:]
    SSA.process_server_response_seed(bytearray.fromhex(server_res_seed))

    sa_response_dict['server_res_seed'] = server_res_seed

    return sa_response_dict


def calculate_authentication_data(dut: Dut, message):
    """
    Calculate message authentication data using Crypto AES-128-CMAC algorithm
    Args:
        dut (Dut): An instance of Dut
        message (str): security access message
    Returns:
        calculated_cmac (str): Calculated authentication data
    """
    # Get 128 bits auth_key from config
    key_128 = bytes.fromhex(dut.conf.default_rig_config['auth_key'])
    cipher_obj = CMAC.new(key_128, ciphermod=AES)
    cipher_obj.update(bytes.fromhex(message))
    calculated_cmac = cipher_obj.hexdigest().upper()

    return calculated_cmac


def step_1(dut: Dut):
    """
    action: Set to programming session, security access to ECU and get request seed message
    expected_result: Security access should be granted in programming session
    """
    # Set to programming session
    dut.uds.set_mode(2)

    # Sleep time to avoid NRC37
    time.sleep(5)
    request_seed_msg = security_access(dut)
    if request_seed_msg is None:
        logging.error("Test Failed: Security access not successful")
        return False, None

    return True, request_seed_msg


def step_2(dut: Dut, req_seed_msg, req_seed_pos):
    """
    action: Calculate and verify client request seed CMAC
    expected_result: Successful verification of client request seed CMAC
    """
    calculated_cmac = calculate_authentication_data(dut, req_seed_msg[:req_seed_pos['rand_end']])
    req_seed_cmac = req_seed_msg[req_seed_pos['cmac_start']:]
    if calculated_cmac == req_seed_cmac:
        logging.info("Client request seed CMAC verification successful")
        return True

    logging.error("Test Failed: Client request seed CMAC verification failed expected %s, "
                  "calculated CMAC %s", req_seed_cmac, calculated_cmac)
    return False


def step_3(dut: Dut, response_seed):
    """
    action: Verify Server response seed with positive response '67'
    expected_result: Successful verification of server response seed
    """
    # pylint: disable=unused-argument
    if response_seed[0:2] == '67':
        logging.info("Server response seed message verified successfully")
        return True

    logging.error("Test Failed: Server response seed verification failed expected 67, "
                  "received %s", response_seed)
    return False


def run():
    """
    Calculate authentication data using Crypto AES-128-CMAC algorithm and verify with
    clientRequestSeed authentication data and server response seed positive response(67)
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'client_seed_pos': {}}

    try:
        dut.precondition(timeout=40)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameter not found")

        result_step, sa_message = dut.step(step_1, purpose="Security access to ECU and get "
                                                           "client request seed message")
        if result_step:
            result_step = dut.step(step_2, sa_message['client_req_seed'],
                                   parameters['client_seed_pos'],
                                   purpose="Verify client request seed CMAC")
        if result_step:
            result_step = dut.step(step_3, sa_message['server_res_seed'],
                                           purpose="Verify server response seed message")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
