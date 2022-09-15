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
    delay timer is activated at every start (boot) i.e- ECU reset or power on. for all supported
    security access levels.
    Steps-
    - Two consecutive false security access attempts and activate delay timer
    - Verify delay timer is activated after false security access attempts
    - Verify delay timer is expired after false security access timeout(10 seconds)
    - ECU hard reset and verify delay timer is activated
    - Verify delay timer is expired after ECU reset timeout(5 seconds)

"""

import logging
import time
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_file_io import SupportFileIO

SIO = SupportFileIO()
SSA = SupportSecurityAccess()


def security_access_invalid_key(dut: Dut, sa_level):
    """
    Security access to ECU with invalid key (corrupt the payload) for negative response
    Args:
        dut(class object): Dut instance
        sa_level (str): security access level
    Returns:
        Response(str): Can response
    """
    sa_keys = dut.conf.default_rig_config
    SSA.set_keys(sa_keys)
    SSA.set_level_key(int(sa_level,16))
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


def security_access_request_seed(dut: Dut, sa_level):
    """
    Security Access request seed
    Args:
        dut (Dut): Dut instance
        sa_level (str): security access level
    Returns: Seed response
    """
    sa_keys = dut.conf.default_rig_config
    SSA.set_keys(sa_keys)
    SSA.set_level_key(int(sa_level,16))
    client_req_seed = SSA.prepare_client_request_seed()
    response = dut.uds.generic_ecu_call(client_req_seed)
    # Server response seed
    return response.raw


def activate_sa_delay_timer(dut, sa_level, session):
    """
    Activate Security access delay timer with invalid key
    Args:
        dut (Dut): Dut instance
        sa_level (str): security access level
        session (int): diagnostic session
    Returns:
        (bool): True
    """
    response = security_access_invalid_key(dut, sa_level)
    # Extract server response and compare with invalidKey(35)
    if response[2:4] != '7F' or response[6:8] != '35':
        logging.error("Test failed: Expected 35, received %s for SA level %s in session %s",
                      response, sa_level, session)
        return False

    response = security_access_invalid_key(dut, sa_level)
    # Extract server response and compare with exceedNumberOfAttempt(36)
    if response[2:4] != '7F' or response[6:8] != '36':
        logging.error("Test failed: Expected 36, received %s for SA level %s in session %s",
                      response, sa_level, session)
        return False

    logging.info("Received %s for SA level %s in session %s as expected", response[6:8],
                 sa_level, session)
    return True


def verify_sa_delay_timer_activated(dut, sa_level, security_access_delay, session):
    """
    Verify Security access delay timer is activated
    Args:
        dut (Dut): Dut instance
        sa_level (str): security access level
        security_access_delay (int): security access time delay
        session (int): diagnostic session
    Returns:
        (bool): True
    """
    # wait for 8 seconds after 2 false security access attempts
    time.sleep(security_access_delay - 2)
    response = security_access_request_seed(dut, sa_level)

    # Extract server response and compare with requiredTimeDelayNotExpired(37)
    if response[2:4] != '7F' or response[6:8] != '37':
        logging.error("Test failed: Expected 37, received %s for SA level %s in session %s",
                      response, sa_level, session)
        return False

    time.sleep(4)
    logging.info("Received %s for SA level %s in session %s as expected", response[6:8],
                 sa_level, session)
    return True


def verify_delay_timer_after_reset(dut, session, sa_level, ecu_reset_delay):
    """
    ECU reset and verify delay timer is activated
    Args:
        dut (Dut): Dut instance
        session (int): diagnostic session
        sa_level (str): security access level
        ecu_reset_delay (int): ECU reset delay
    Returns:
        (bool): True
    """
    dut.uds.ecu_reset_1101()
    dut.uds.set_mode(session)
    # wait for 4 seconds after ECU reset
    time.sleep(ecu_reset_delay - 1)
    response = security_access_request_seed(dut, sa_level)
    # Extract server response and compare with requiredTimeDelayNotExpired (37)
    if response[2:4] != '7F' or response[6:8] != '37':
        logging.error("Test failed: Expected 37, received %s for SA level %s in session %s",
                      response, sa_level, session)
        return False

    time.sleep(2)

    logging.info("Received %s for SA level %s in session %s as expected", response[6:8],
                 sa_level, session)
    return True


def verify_delay_timer_expired(dut, sa_level, session):
    """
    Verify delay timer is expired
    Args:
        dut (Dut): Dut instance
        sa_level(str): security access level
        session (int): diagnostic session
    Returns:
        (bool): True
    """
    response = security_access_request_seed(dut, sa_level)
    # Extract server response and compare with positive response (67)
    if response[4:6] != '67':
        logging.error("Test failed: Expected 67, received %s for SA level %s in session %s",
                      response, sa_level, session)
        return False
    logging.info("Received %s for SA level %s in session %s as expected", response[4:6],
                 sa_level, session)
    return True


def step_1(dut: Dut, parameters):
    """
    action: Verify security access delay timer is activated in programming session
            and expired after after delay for supported security levels
    expected_result: True on successfully verified security access delay timer.
    """
    results = []

    # Sleep time to avoid NRC37
    time.sleep(5)

    for sa_level in parameters['sa_level_programming']:

        result_sa_delay_timer = activate_sa_delay_timer(dut, sa_level, session=2)

        result_activated = result_sa_delay_timer and \
            verify_sa_delay_timer_activated(dut, sa_level, parameters['security_access_delay'],
                                            session=2)

        result_expired = result_activated and verify_delay_timer_expired(dut, sa_level, session=2)

        results.append(result_expired)
        time.sleep(parameters['security_access_level_check_delay'])

    if all(results) and len(results) == len(parameters['sa_level_programming']):
        logging.info("Successfully verified delay timer for all SA levels in programming session")
        return True

    logging.error("Test failed: Security access delay timer verification failed for some "
                    "or all SA levels")
    return False


def step_2(dut: Dut, parameters):
    """
    action: Verify ECU reset delay timer is activated in programming session
            and expired after delay for supported security levels
    expected_result: True on successfully verified ECU reset delay timer.
    """
    results = []
    for sa_level in parameters['sa_level_programming']:

        result_sa_delay_timer = verify_delay_timer_after_reset(dut, session=2, sa_level=sa_level,
                                                    ecu_reset_delay=parameters['ecu_reset_delay'])

        result_expired = result_sa_delay_timer and verify_delay_timer_expired(dut, sa_level,
                                                                                session=2)

        results.append(result_expired)
        time.sleep(parameters['security_access_level_check_delay'])

    if all(results) and len(results) == len(parameters['sa_level_programming']):
        logging.info("Successfully verified delay timer for all SA levels in programming"
                    " session")
        return True

    logging.error("Test failed: Security access delay timer verification failed for some"
                    " or all SA levels")
    return False


def step_3(dut: Dut, parameters):
    """
    action: Verify security access delay timer is activated in extended session
            and expired after delay for supported security levels
    expected_result: True on successfully verified security access delay timer.
    """
    dut.uds.set_mode(1)
    dut.uds.set_mode(3)

    results = []
    for sa_level in parameters['sa_level_extended']:

        result_sa_delay_timer = activate_sa_delay_timer(dut, sa_level, session=3)

        result_activated = result_sa_delay_timer and \
            verify_sa_delay_timer_activated(dut, sa_level, parameters['security_access_delay'],
                                            session=3)

        result_expired = result_activated and verify_delay_timer_expired(dut, sa_level, session=3)

        results.append(result_expired)
        time.sleep(parameters['security_access_level_check_delay'])

    if all(results) and len(results) == len(parameters['sa_level_extended']):
        logging.info("Successfully verified delay timer for all SA levels in extended session")
        return True

    logging.error("Test failed: Security access delay timer verification failed for some or"
                  " all SA levels")
    return False


def step_4(dut: Dut, parameters):
    """
    action: Verify ECU reset delay timer is activated in extended session and expired after delay
            for supported security levels
    expected_result: True on successfully verified ECU reset delay timer.
    """
    results = []
    for sa_level in parameters['sa_level_extended']:

        result_sa_delay_timer = verify_delay_timer_after_reset(dut, session=3, sa_level=sa_level,
                                                    ecu_reset_delay=parameters['ecu_reset_delay'])

        result_expired = result_sa_delay_timer and verify_delay_timer_expired(dut, sa_level,
                                                                              session=3)

        results.append(result_expired)
        time.sleep(parameters['security_access_level_check_delay'])

    if all(results) and len(results) == len(parameters['sa_level_extended']):
        logging.info("Successfully verified delay timer for all security access levels "
                     "in extended session")
        return True

    logging.error("Test failed: Security access delay timer verification failed for some or"
                  " all security access levels")
    return False


def run():
    """
    Verify false attempt security access delay timer and ECU reset delay timer is activated or not
    for both programming and extended session for all supported security levels.
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False
    # Read yml parameters
    parameters_dict = {'security_access_delay': 0,
                        'ecu_reset_delay': 0,
                       'security_access_level_check_delay': 0,
                       'sa_level_programming': [],
                       'sa_level_extended': []
                       }
    try:
        dut.precondition(timeout=300)
        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameter not found")

        result_step = dut.step(step_1, parameters, purpose="Verify security access delay timer is"
                                " activated in programming session and expired after delay for"
                                " supported security levels")

        if result_step:
            result_step = dut.step(step_2, parameters, purpose="Verify ECU reset delay timer is"
                                    " activated in programming session and expired after delay"
                                    " for supported security levels")

        if result_step:
            result_step = dut.step(step_3, parameters, purpose="Verify security access delay timer"
                                    " is activated in extended session and expired after delay for"
                                    " supported security levels")

        if result_step:
            result_step = dut.step(step_4, parameters, purpose="Verify ECU reset delay timer is"
                                    " activated in extended session and expired after delay for"
                                    " supported security levels")

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
