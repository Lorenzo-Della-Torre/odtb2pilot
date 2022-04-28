"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 469134
version: 1
title: Default values - Delay timers and counters for false attempts
purpose: >
    To define default values for the parameters used to configure the level of protection

description: >
    The default values for below parameters shall be set to;
	- Delay Timer activated after a number of false Security Access attempts; 10 seconds.
	- Delay Timer activated at every start (boot), e.g. ECU reset/power on; 5 seconds.
	- Number of false Security Access attempt before a delay time is activated; 2 (i.e.
	  delay timer activated at the second failed attempt).

    The information of actual number of false attempts (i.e. delay timer status active or not)
    shall be immediately stored in non-volatile memory. The counter for false attempts can be
    used to determine whether the ‘delay timer activated after a number of false attempts’
    shall be invoked also at every start or if only the ‘delay timer activated at every start”
    shall be applied.

    When the delay at start is active, the ECU shall upon a security access request
    (clientRequestSeed) report to the diagnostic tester just like when the delay timer
    is activated due to a number of false attempts (requiredTimeDelayNotExpired).

    Example.
        ...
        time 5001 ms- Tester -> ECU- Request 'Seed'
        time 5002 ms- Tester <- ECU- Response 'Seed'
        time 5003 ms- Tester -> ECU- Request 'ECU Reset" (ECU restarts)
        time 5004 ms- Tester -> ECU- Request 'Seed'
        time 5005 ms- Tester <- ECU- Negative Response 'requiredTimeDelayNotExpired'
                                    - delay timer at start is active.
        ...
        time 10004 ms- Tester -> ECU- Request 'Seed' (delay timer at start has expired)
        time 10005 ms- Tester <- ECU- Response 'Seed'
        time 10006 ms- Tester -> ECU- Request 'Seed'
        time 10007 ms- Tester <- ECU- Response 'Seed'

    Notes.
    - Each Security Access level is handled independently.
    - Delay timers must not reset when activated for one level but client restarts a Security
      Access session for another level.

details: >
    Verify the delay timer is activated after two false security access attempts and also verify
    delay timer is activated at every start (boot) i.e- ECU reset or power on.
    Steps-
    - Two consecutive false security access attempts and activate delay timer
    - Verify delay timer is activated after false security access attempts
    - Verify delay timer is expired after false security access timeout(10 seconds)
    - ECU hard reset and verify delay timer is activated
    - Verify delay timer is expired after ECU reset timeout(5 seconds)

"""

import logging
import time
from hilding.conf import Conf
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_file_io import SupportFileIO

SIO = SupportFileIO()
SSA = SupportSecurityAccess()
CNF = Conf()


def security_access_invalid_key(dut: Dut):
    """
    Security access to ECU with invalid key (corrupt the payload) for negative response
    Args:
        dut(class object): Dut instance
    Returns:
        Response(str): Can response
    """
    sa_keys = CNF.default_rig_config
    SSA.set_keys(sa_keys)
    SSA.set_level_key(1)
    client_req_seed = SSA.prepare_client_request_seed()
    response = dut.uds.generic_ecu_call(client_req_seed)

    # Prepare server response seed
    server_res_seed = response.raw[4:]
    SSA.process_server_response_seed(bytearray.fromhex(server_res_seed))

    client_send_key = SSA.prepare_client_send_key()
    # Corrupt payload
    client_send_key[4] = 0xFF
    client_send_key[5] = 0xFF

    response = dut.uds.generic_ecu_call(client_send_key)

    SSA.process_server_response_key(bytearray.fromhex(response.raw[6:(6+4)]))
    # Server response
    return response.raw


def security_access_request_seed(dut: Dut):
    """
    Security Access request seed
    Args:
        dut (class object): Dut instance
    Returns: Seed response
    """
    sa_keys = CNF.default_rig_config
    SSA.set_keys(sa_keys)
    SSA.set_level_key(1)
    client_req_seed = SSA.prepare_client_request_seed()
    response = dut.uds.generic_ecu_call(client_req_seed)
    # Server response seed
    return response.raw


def step_1(dut: Dut):
    """
    action: Set ECU to programming session and activate delay timer after two consecutive
            false security access attempts.
    expected_result: Negative response requestOutOfRange(31) and exceedNumberOfAttempt(36)
    """
    dut.uds.set_mode(2)
    delay_timer_start = 0.0
    result = []
    response = security_access_invalid_key(dut)
    if response is not None:
        # Extract server response and compare with requestOutOfRange(31)
        if response[6:8] == '31':
            result.append(True)
        else:
            logging.error("Invalid response received %s, expected 31", response[6:8])
            result.append(False)
    else:
        logging.error("Test Failed: Empty response of security access")
        return False, None

    response = security_access_invalid_key(dut)
    if response is not None:
        # Extract server response and compare with exceedNumberOfAttempt(36)
        if response[6:8] == '36':
            result.append(True)
            delay_timer_start = time.time()
        else:
            logging.error("Invalid response received %s, expected 36", response[6:8])
            result.append(False)
    else:
        logging.error("Test Failed: Empty response of security access")
        return False, None

    if len(result) != 0 and all(result):
        return True, delay_timer_start

    logging.error("Test Failed: Delay timer is not activated")
    return False, None


def step_2(dut: Dut, delay_timer_start):
    """
    action: Verify security access delay timer is activated with clientRequestSeed response
    expected_result: Negative response requiredTimeDelayNotExpired(37)
    """
    # Read yml parameters
    parameters_dict = {'security_access_delay': '',
                       'ecu_reset_delay': ''}
    parameters = SIO.parameter_adopt_teststep(parameters_dict)
    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False, None

    delay_timer_end = time.time()
    elapsed_time = delay_timer_end - delay_timer_start

    if elapsed_time <= parameters['security_access_delay']:
        response = security_access_request_seed(dut)
        if response is None:
            logging.error("Test Failed: Empty response")
            return False, None
        # Extract server response and compare with requiredTimeDelayNotExpired(37)
        if response[6:8] == '37':
            return True, parameters

        logging.error("Test Failed: Invalid response received %s, expected 37", response[6:8])
        return False, None

    logging.error("Test Failed: Security access delay timer %s is greater than elapsed time %s",
                  parameters['security_access_delay'], elapsed_time)
    return False, None


def step_3(dut: Dut, delay_timer_start, parameters):
    """
    action: Verify security access delay timer is expired with clientRequestSeed response
    expected_result: Positive response(67)
    """
    # Reset security access delay timer
    delay_timer_end = time.time()
    delay_timer_elapsed = delay_timer_end - delay_timer_start
    if delay_timer_elapsed <= parameters['security_access_delay']:
        time.sleep(parameters['security_access_delay'] + 0.1 - delay_timer_elapsed)

    response = security_access_request_seed(dut)
    if response is None:
        logging.error("Test Failed: Empty response")
        return False
    # Extract server response and compare with positive response (67)
    if response[4:6] == '67':
        return True
    logging.error("Test Failed: Security Access response received %s, expected 67", response[4:6])
    return False


def step_4(dut: Dut, parameters):
    """
    action: Set ECU to programming session and verify delay timer is activated
            or not after ECU reset
    expected_result: Negative response requiredTimeDelayNotExpired(37)
    """
    delay_timer_start = time.time()
    dut.uds.generic_ecu_call(bytes.fromhex('1101'))
    dut.uds.generic_ecu_call(bytes.fromhex('1002'))
    delay_timer_end = time.time()
    elapsed_time = delay_timer_end - delay_timer_start

    delay_timer_start = time.time()
    if elapsed_time <= parameters['ecu_reset_delay']:
        response = security_access_request_seed(dut)
        if response is None:
            logging.error("Test Failed: Empty response")
            return False, None
        # Extract server response and compare with requiredTimeDelayNotExpired (37)
        if response[6:8] == '37':
            return True, delay_timer_start

        logging.error("Test Failed: Invalid response received %s, expected 37", response[6:8])
        return False, None

    logging.error("Test Failed: ECU delay timer %s is less than elapsed time %s",
                  parameters['ecu_reset_delay'], elapsed_time)
    return False, None


def step_5(dut: Dut, delay_timer_start, parameters):
    """
    action: Verify ECU start delay timer is expired with clientRequestSeed response
    expected_result: Positive response (67)
    """
    dut.uds.set_mode(2)
    # Reset security access delay timer
    delay_timer_end = time.time()
    delay_timer_elapsed = delay_timer_end - delay_timer_start

    if delay_timer_elapsed <= parameters['ecu_reset_delay']:
        time.sleep(parameters['ecu_reset_delay'] + 0.1 - delay_timer_elapsed)

    if delay_timer_elapsed > parameters['ecu_reset_delay'] + 1:
        logging.error("Test Failed: Too much time %s seconds has passed after the delay timer "
                      "was activated, therefore it is not possible to validate at which time "
                      "actually delay expired", delay_timer_elapsed)
        return False

    response = security_access_request_seed(dut)
    if response is None:
        logging.error("Test Failed: Empty response")
        return False
    # Extract server response and compare with positive response(67)
    if response[4:6] == '67':
        return True

    logging.error("Test Failed: Security Access response received %s, expected 67", response[4:6])
    return False


def run():
    """
    Verify false attempt security access delay timer and ECU reset delay timer is activated or not
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=60)
        result_step, delay_timer_start = dut.step(step_1, purpose="Activate false attempts "
                                                  "Security Access delay timer")
        if result_step:
            result_step, parameters = dut.step(step_2, delay_timer_start, purpose="Verify "
                                               "security access delay timer is activated")
        if result_step:
            result_step = dut.step(step_3, delay_timer_start, parameters,
                                   purpose="Verify security access delay timer is expired")
        if result_step:
            result_step, delay_timer_start = dut.step(step_4, parameters, purpose="Verify "
                                                      "ECU reset delay timer is activated")
        if result_step:
            result_step = dut.step(step_5, delay_timer_start, parameters, purpose="Verify "
                                   "startup delay timer is expired")

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
