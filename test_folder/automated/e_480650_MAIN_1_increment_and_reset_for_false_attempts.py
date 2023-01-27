"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 480650
version: 1
title: Increment and reset counters for false attempts

purpose: >
    Define conditions for counter for false attempts, when to increment and when to reset.

description: >
    Per every supported security access subfunction pair (“requestSeed/sendKey” pair),
    i.e. per security access level, the server shall implement separate counter(s) for
    the current number of false attempts. The counter for a specific security access
    level shall only be reset when;
    •  A valid clientSendKey request message is received, i.e. resulting in a positive response.
    •  The delay timer activated after a number of false attempts expires.
    The counter for false attempts shall be incremented when no delay timer is active and;
    •  The authentication_data, message_id or client_proof_of_ownership verification
       fails for the clientSendKey message.

details: >
    Verify false attempts security access delay timer is activated and expired
    Steps-
    1. False security access attempts twice and verify delay timer is activated
    2. Request seed and verify security access delay timer is not expired
    3. Security access attempt with valid key and verify delay timer is expired
    4. Repeat above steps for all supported security access level in supported session
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_file_io import SupportFileIO

SIO = SupportFileIO()
SSA = SupportSecurityAccess()


def security_access_request_seed(dut, sa_level):
    """
    Security access request seed
    Args:
        dut (Dut): An instance of Dut
        sa_level (str): Security access level
    Returns:
        response.raw (str): Request seed response
    """
    SSA.set_keys(sa_keys = dut.conf.default_rig_config)
    SSA.set_level_key(int(sa_level, 16))
    client_req_seed = SSA.prepare_client_request_seed()
    response = dut.uds.generic_ecu_call(client_req_seed)
    return response.raw


def security_access(dut, sa_level, invalid_key_flag=False):
    """
    Security access to ECU
    Args:
        dut (Dut): An instance of Dut
        sa_level (str): Security Access level
        invalid_key_flag (bool): True for security access with invalid key
    Returns:
        response.raw (str): Response of send key
    """
    SSA.set_keys(sa_keys = dut.conf.default_rig_config)
    SSA.set_level_key(int(sa_level, 16))
    client_req_seed = SSA.prepare_client_request_seed()

    response = dut.uds.generic_ecu_call(client_req_seed)

    server_res_seed = response.raw[4:]
    SSA.process_server_response_seed(bytearray.fromhex(server_res_seed))
    client_send_key = SSA.prepare_client_send_key()

    # Corrupt payload for security access with invalid key
    if invalid_key_flag:
        client_send_key[4] = 0xFF
        client_send_key[5] = 0xFF

    response = dut.uds.generic_ecu_call(client_send_key)

    SSA.process_server_response_key(bytearray.fromhex(response.raw[6:(6+4)]))
    return response.raw


def activate_sa_delay_timer(dut, sa_level):
    """
    Activate security access delay timer
    Args:
        dut (Dut): An instance of Dut
        sa_level(str): Security Access level
    Returns: True when security access delay timer is activated
    """
    # Security access with invalid key
    response = security_access(dut, sa_level, invalid_key_flag=True)
    if response[2:4] != '7F' and response[6:8] != '35':
        logging.error("Expected negative response '7F' and NRC-35(invalidKey) for security access "
                      "with invalid key, but received %s for level %s", response, sa_level)
        return False

    logging.info("Received negative response '7F' and NRC-35(invalidKey) for security "
                 "access with invalid key for level %s as expected", sa_level)

    # Security access with invalid key for second time
    response = security_access(dut, sa_level, invalid_key_flag=True)
    if response[2:4] != '7F' and response[6:8] != '36':
        logging.error("Expected negative response '7F' and NRC-36(exceededNumberOfAttempts) for "
                      "security access with invalid key, but received %s", response)
        return False

    logging.info("Security access delay timer is activated for level %s", sa_level)
    return True


def verify_sa_delay_timer_not_expired(dut, sa_level):
    """
    Verify security access delay timer is not expired for supported security access level.
    Args:
        dut (Dut): An instance of Dut
        sa_level (int): Security Access level
    Returns: True when security access delay timer is not expired
    """
    # Request seed to verify delay timer is not expired
    response = security_access_request_seed(dut, sa_level)
    if response[2:4] == '7F' and response[6:8] == '37':
        logging.info("Received NRC-37(requiredTimeDelayNotExpired) for level %s", sa_level)
        return True

    logging.error("Test Failed: Expected NRC-37(requiredTimeDelayNotExpired), but received %s for "
                  "level %s", response, sa_level)
    return False


def verify_sa_delay_timer_expired(dut, sa_level):
    """
    Verify security access delay timer for supported security access level.
    Args:
        dut (Dut): An instance of Dut
        sa_level (int): Security access level
    Returns: True when successfully verified security access delay timer is expired
    """
    # Time sleep to verify security access delay timer is expired
    time.sleep(10)

    response = security_access(dut, sa_level, invalid_key_flag=False)
    if response[2:4] == '67':
        logging.info("Security access delay timer is expired as expected for level %s", sa_level)
        return True

    logging.error("Test Failed: Expected security access delay timer to expire for level %s,"
                  " but received %s", sa_level, response)
    return False


def step_1(dut: Dut, parameters):
    """
    action: Set ECU to programming session and verify security access delay timer for supported
            security access level(01, 19) in programming session
    expected_result: Security access delay timer should be activated and expired properly for
                     supported security access level(01, 19) in programming session
    """
    # Set ECU to programming session
    dut.uds.set_mode(2)

    # Time sleep to avoid NRC-37
    time.sleep(5)

    results = []

    for sa_level in parameters['sa_level_programming']:
        activate_timer = activate_sa_delay_timer(dut, sa_level)
        not_activate_timer = activate_timer and verify_sa_delay_timer_not_expired(dut, sa_level)
        delay_timer_expired = not_activate_timer and verify_sa_delay_timer_expired(dut, sa_level)
        results.append(delay_timer_expired)

    if len(results) > 0 and all(results):
        logging.info("Successfully verified security access delay timer for security access with "
                     "invalid key in programming session")
        return True

    logging.error("Test Failed: Security access delay timer for security access with invalid key "
                  "is not proper in programming session")
    return False


def step_2(dut: Dut, parameters):
    """
    action: Set ECU to extended session and verify security access delay timer for supported
            security access level(05, 19, 23, 27)
    expected_result: Security access delay timer should be activated and expired properly for
                     supported security access level(05, 19, 23, 27) in extended session
    """
    # Set ECU in extended session
    dut.uds.set_mode(1)
    dut.uds.set_mode(3)

    time.sleep(2)

    results = []

    for sa_level in parameters['sa_level_extended']:
        activate_timer = activate_sa_delay_timer(dut, sa_level)
        not_activate_timer = activate_timer and verify_sa_delay_timer_not_expired(dut, sa_level)
        delay_timer_expired = not_activate_timer and verify_sa_delay_timer_expired(dut, sa_level)
        results.append(delay_timer_expired)

    if all(results) and len(results) > 0:
        logging.info("Successfully verified security access delay timer for security access with "
                     "invalid key in extended session")
        return True

    logging.error("Test Failed: Security access delay timer for security access with invalid key "
                  "is not proper in extended session")
    return False


def run():
    """
    Verify security access delay timer for security access with invalid key is activated and
    expired properly in programming and extended session for all supported security access level
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'sa_level_programming': [],
                       'sa_level_extended': []}

    try:
        dut.precondition(timeout=200)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError('yml parameters not found')

        result_step = dut.step(step_1, parameters, purpose='Verify security access delay timer for'
                               ' supported security access level(01, 19) in programming session')
        if result_step:
            result_step = dut.step(step_2, parameters, purpose='Verify security access delay '
                                  'timer for supported security access level(05, 19, 23, 27) in '
                                  'extended session')
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
