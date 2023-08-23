"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 480619
version: 1
title: Initialization vectors
purpose: >
    The combination of encryption key and initialization vector (IV) must only
    be invoked once, for IV constructions in authentication method 0x0001.

description: >
    All used initilization vectors must be unique per every new encrypt request.

    Note-
    For AES encryption in counter mode (AES-128-CTR), the recommended implementation
    is to generate a cryptographically secure random number.

    Other alternative is to divide the initialization vector into two parts, where the
    first part is the random number that is generated per every new encryption request
    and the second part is a counter (always incrementing, hence the last valid counter
    value shall be stored in non-volatile memory).

    A maximum of two consecutive blocks are encrypted in the Security Access Generation
    2 protocol. Special care should be taken to ensure that the generated Initialization
    Vector doesn’t overflow to avoid unexpected behavior of different system implementations.

    For example, an IV generated for the first block should not contain the maximum value
    (i.e. all 0xFF), otherwise the incremented IV for the second block may become an
    unexpected value. One possible way to avoid IV overflow is to clear the least
    significant byte (LSB) of the initial IV to zero.


details: >
    Security access to ECU and check initialization vectors per every new encrypt request
    are unique.

"""

import logging
from hilding.dut import DutTestError
from hilding.dut import Dut
from hilding.conf import Conf
from supportfunctions.support_sec_acc import SupportSecurityAccess

SSA = SupportSecurityAccess()
CNF = Conf()


def security_access_subfunction(dut: Dut):
    """
    Security access to ECU and get the initialization vector
    per every new encrypt request
    Args:
        dut(class object): Dut instance
    Returns:
        iv(dict): dictionary of initialization vectors for all encrypt request
    """
    iv_dict = {'request_seed': '',
               'response_seed': '',
               'send_key': ''
               }
    SSA.set_keys(CNF.default_rig_config)
    SSA.set_level_key(1)
    client_req_seed = SSA.prepare_client_request_seed()
    response = dut.uds.generic_ecu_call(client_req_seed)

    server_res_seed = response.raw[4:]
    result = SSA.process_server_response_seed(
        bytearray.fromhex(server_res_seed))

    client_send_key = SSA.prepare_client_send_key()
    dut.uds.generic_ecu_call(client_send_key)

    result = SSA.process_server_response_key(
        bytearray.fromhex(response.raw[6:(6+4)]))

    client_req_seed = client_req_seed.hex().upper()
    client_send_key = client_send_key.hex().upper()
    # Initialization vector start and end index
    # For clientRequestSeed & clientSendKey 12:44
    # For serverResponseSeed 8:40
    iv_dict['request_seed'] = client_req_seed[12:44]
    iv_dict['response_seed'] = server_res_seed[8:40]
    iv_dict['request_key'] = client_send_key[12:44]

    if result != 0:
        logging.error("Security Access to ECU not successful")
        return None
    return iv_dict


def step_1(dut: Dut):
    """
    action: Security Access to ECU and get initialization vectors
            of clientRequestSeed, serverResponseSeed and clientSendKey.
    expected_result: Positive response with initialization vector dictionary

    """
    dut.uds.set_mode(2)
    iv_dict = security_access_subfunction(dut)
    if iv_dict['request_seed'] != '' \
            and iv_dict['response_seed'] != '' \
            and iv_dict['request_key'] != '':
        return True, iv_dict
    logging.error("Test Failed: Security Access to ECU not successful")
    return False, None


def step_2(dut: Dut):
    """
    action: Security Access to ECU again and get initialization vectors
            of clientRequestSeed, serverResponseSeed and clientSendKey.
    expected_result: Positive response with initialization vector dictionary

    """
    dut.uds.set_mode(2)
    iv_dict = security_access_subfunction(dut)
    if iv_dict['request_seed'] != '' \
            and iv_dict['response_seed'] != '' \
            and iv_dict['request_key'] != '':
        return True, iv_dict
    logging.error("Test Failed: Security Access to ECU not successful")
    return False, None


def step_3(dut: Dut, iv_dict_prev, iv_dict_curr):
    """
    action: Compare initialization vectors of previous security access to
        ECU with current security access to ECU and check IV's are unique
        per every new encrypt request.
    expected_result: positive response
    """
    dut.uds.set_mode()
    if iv_dict_prev['request_seed'] != iv_dict_curr['request_seed'] \
            and iv_dict_prev['response_seed'] != iv_dict_curr['response_seed']\
            and iv_dict_prev['request_key'] != iv_dict_curr['request_key']:
        return True
    logging.error("Test failed: Initialization vectors are "
                  "not unique per new encrypt request")
    return False


def run():
    """ Check all used initialization vectors are unique per every new encrypt request """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition()
        result_step, iv_prev = dut.step(step_1,
                                        purpose="Security access to ECU "
                                        "and get IVs of encrypt request")
        if result_step:
            result_step, iv_curr = dut.step(step_2,
                                            purpose="Security access to ECU again "
                                            "and get IVs of encrypt request")
        if result_step:
            result_step = dut.step(step_3, iv_prev, iv_curr,
                                   purpose="Compare previous IVs with current IVs "
                                   "and check IVs are unique per every encrypt request")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
