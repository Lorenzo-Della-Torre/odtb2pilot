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
    •	A valid clientSendKey request message is received, i.e. resulting in a positive response.
    •	The delay timer activated after a number of false attempts expires.
    The counter for false attempts shall be incremented when no delay timer is active and;
    •	The authentication_data, message_id or client_proof_of_ownership verification
        fails for the clientSendKey message.

details: >
    Verify false attempts security access delay timer is activated and expired
    Steps-
    1. False security access attempts twice and verify delay timer is activated
    2. Request seed and verify security access delay timer is not expired
    3. Security access attempt with valid key and verify delay timer is expired
    4. Repeat above steps for all supported security access level in supported session
"""


import logging
import time
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_file_io import SupportFileIO

SIO = SupportFileIO()
SSA = SupportSecurityAccess()


def security_access_request_seed(dut: Dut):
    """
    Security Access request seed
    Args:
        dut (Dut): An instance of Dut
    Returns: Seed response
    """
    sa_keys = dut.conf.default_rig_config
    SSA.set_keys(sa_keys)
    SSA.set_level_key(1)
    client_req_seed = SSA.prepare_client_request_seed()
    response = dut.uds.generic_ecu_call(client_req_seed)
    # Server response seed
    return response.raw


def security_access(dut: Dut, sa_level, invalid_key_flag=False):
    """
    Security access to ECU
    Args:
        dut(class object): Dut instance
        sa_level(str): Security Access level
        invalid_key_flag(bool): True to false security access attempts
    Returns:
        Response(str): Can response
    """
    sa_keys = dut.conf.default_rig_config
    SSA.set_keys(sa_keys)
    SSA.set_level_key(int(sa_level, 16))
    client_req_seed = SSA.prepare_client_request_seed()
    response = dut.uds.generic_ecu_call(client_req_seed)

    # Prepare server response seed
    server_res_seed = response.raw[4:]
    SSA.process_server_response_seed(bytearray.fromhex(server_res_seed))

    client_send_key = SSA.prepare_client_send_key()
    # Corrupt payload for false security access attempts
    if invalid_key_flag:
        client_send_key[4] = 0xFF
        client_send_key[5] = 0xFF

    response = dut.uds.generic_ecu_call(client_send_key)

    SSA.process_server_response_key(bytearray.fromhex(response.raw[6:(6+4)]))
    # Server response
    return response.raw


def activate_sa_delay_timer(dut, sa_level):
    """
    Activate security Access delay timer
    Args:
        dut (class object): Dut instance
        sa_level(str): Security Access level
    Returns: True when security access delay timer is activated
    """
    result = []
    # Security access attempt with invalid key
    response = security_access(dut, sa_level, invalid_key_flag=True)
    if response is not None:
        # Extract server response and compare with 7F and requestOutOfRange(31)
        if response[2:4] == '7F' and response[6:8] == '31':
            result.append(True)
        else:
            logging.error("Invalid response received %s, expected NRC 31", response)
            result.append(False)
    else:
        logging.error("Test Failed: Invalid or empty response of security access")
        return False

    # Security access attempt with invalid key
    response = security_access(dut, sa_level, invalid_key_flag=True)
    if response is not None:
        # Extract server response and compare with 7F and exceedNumberOfAttempt(36)
        if response[2:4] == '7F' and response[6:8] == '36':
            result.append(True)
        else:
            logging.error("Invalid response received %s, expected NRC 36", response)
            result.append(False)
    else:
        logging.error("Test Failed: Invalid or empty response of security access")
        return False

    if len(result) != 0 and all(result):
        logging.info("Security access delay timer is activated for level %s", sa_level)
        return True

    logging.error("Test Failed: Security access delay timer is not activated for level %s",
                  sa_level)
    return False


def verify_sa_delay_timer_not_expired(dut: Dut, sa_level):
    """
    Verify security access delay timer is not expired for supported security access level.
    Args:
        dut (Dut): An instance of Dut
        sa_level(int): Security Access level
    Returns: True when security access delay timer is not expired
    """
    # Request seed to verify delay timer is not expired
    response = security_access_request_seed(dut)
    if response is None:
        logging.error("Test Failed: Empty response")
        return False, None

    # Extract server response and compare with 7F and requiredTimeDelayNotExpired(37)
    if response[2:4] == '7F' and response[6:8] == '37':
        logging.info("Security access requiredTimeDelayNotExpired(%s) for level %s",
                     response[6:8], sa_level)
        return True

    logging.error("Test Failed: Expected requiredTimeDelayNotExpired(37), received %s for "
                  "level %s", response, sa_level)
    return False


def verify_sa_delay_timer_expired(dut: Dut, sa_level):
    """
    Verify security access delay timer for supported security access level.
    Args:
        dut (Dut): An instance of Dut
        sa_level(int): Security Access level
    Returns: True when successfully verified security access delay timer is expired
    """
    # Waite to verify security access delay timer is expired
    time.sleep(10)
    # Security access request with valid key
    response = security_access(dut, sa_level, invalid_key_flag=False)
    # Verify positive response to make sure delay timer is expired
    if response[2:4] == '67':
        logging.info("Security access delay timer is expired as expected")
        return True

    logging.error("Test Failed: Security access delay timer is not expired, response %s", response)
    return False


def step_1(dut: Dut):
    """
    action: Set ECU to programming session and verify false attempts security access
            delay timer is activated for supported security access level(01, 19).
    expected_result: True when security access delay timer is verified in programming session
    """
    dut.uds.set_mode(2)

    # Read yml parameters
    parameters_dict = {'sa_level_programming': '',
                       'sa_level_extended': ''}
    parameters = SIO.parameter_adopt_teststep(parameters_dict)

    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False, None

    results = []
    for sa_level in parameters['sa_level_programming']:
        # Activate security access delay timer
        activate_timer = activate_sa_delay_timer(dut, sa_level)

        # Verify security access requiredTimeDelayNotExpired(37)
        not_activate_timer = activate_timer and verify_sa_delay_timer_not_expired(dut, sa_level)

        # Verify security access delay timer is expired
        delay_timer_expired = not_activate_timer and \
                                verify_sa_delay_timer_expired(dut, sa_level)
        results.append(delay_timer_expired)

    if all(results) and len(results) > 0:
        logging.info("False attempts security access delay time verified successfully "
                    "in programming session")
        return True, parameters

    logging.error("Test Failed: False attempts security access delay time verification failed "
                  "in programming session")
    return False, None


def step_2(dut: Dut, parameters):
    """
    action: Set ECU to programming session and verify false attempts security access
            delay timer is activated for supported security access level(05, 19, 23, 27).
    expected_result: True when security access delay timer is verified in extended session
    """
    dut.uds.set_mode(1)
    dut.uds.set_mode(3)
    time.sleep(2)

    results = []
    for sa_level in parameters['sa_level_extended']:
        # Activate security access delay timer
        activate_timer = activate_sa_delay_timer(dut, sa_level)

        # Verify security access requiredTimeDelayNotExpired(37)
        not_activate_timer = activate_timer and verify_sa_delay_timer_not_expired(dut, sa_level)

        # Verify security access delay timer is expired
        delay_timer_expired = not_activate_timer and \
                                verify_sa_delay_timer_expired(dut, sa_level)
        results.append(delay_timer_expired)

    if all(results) and len(results) > 0:
        logging.info("False attempts security access delay timer verified "
                     "successfully in extended session")
        return True

    logging.error("Test Failed: False attempts security access delay timer verification "
                  "failed in extended session")
    return False


def run():
    """
    Verify false attempt security access delay timer is activated or not in both programming
    and extended session
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=90)
        result_step, parameters = dut.step(step_1, purpose="Verify security access delay timer "
                                           "in programming session")
        if result_step:
            result_step = dut.step(step_2, parameters, purpose="Verify security access delay "
                                   "timer in extended session")

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
