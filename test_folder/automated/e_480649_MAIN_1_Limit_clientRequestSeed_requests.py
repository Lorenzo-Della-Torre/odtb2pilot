"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.


NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/


reqprod: 480649
version: 1
title: Limit clientRequestSeed requests

purpose: >
    To limit the possibility to request infinite number of server random numbers by sending
    multiple clientRequestSeed messages.

description: >
    The server shall limit the number of clientRequestSeed requests for a period of time, by only
    accepting two clientRequestSeed requests within a period of 5 seconds. A third request detected
    within that period of time shall be rejected by a negative response code (conditions not
    correct). There shall be one independent timer per supported security access level.
    The server shall reset any ongoing timer for actual security access level if a valid clientSend
    key for that level is received, i.e. the server is unlocked. ClientRequestSeed messages received
    with invalid length or invalid subfunction shall be rejected with a negative response code only
    i.e. without affecting the number of requests.


details: > Validate Security Access response of clientRequestSeed requests raised within valid time
    of 5000ms.
    Steps-
        1. Set to programming session and Security Access to ECU.
        2. Three consecutive clientRequestSeed within valid time of 5000ms and verify first two
           request are accepted
        3. Verify valid clientSend key is successfully received, to check timer reset
        4. Verify rejection of clientRequestSeed having invalid subfunction with negative response
           code
"""

import logging
import time
from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.conf import Conf
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_service27 import SupportService27

SSA = SupportSecurityAccess()
CNF = Conf()
SC = SupportCAN()
SIO = SupportFileIO()
SE27 = SupportService27()


def security_access_request_seed(dut: Dut, subfunction_flag=False):
    """
    Security Access request seed
    Args:
        dut (Dut): An instance of Dut
        subfunction_flag (bool): Corrupt subfunction when True
    Returns: Seed response
    """
    sa_keys = CNF.default_rig_config
    SSA.set_keys(sa_keys)
    SSA.set_level_key(1)
    client_req_seed = SSA.prepare_client_request_seed()

    # Corrupt subfunction when flag is True
    if subfunction_flag:
        client_req_seed[1] = 0x00

    response = dut.uds.generic_ecu_call(client_req_seed)
    # Server response seed
    return response.raw


def verify_positive_response(response):
    """
    Verify security access request seed positive response
    Args:
        dut (Dut): An instance of Dut
    Returns: True when positive response successfully verified
    """
    # Extract and compare positive response
    if response[4:6] == '67':
        logging.info("Positive response received %s as expected", response[4:6])
        return True

    logging.error("Expected positive response 67, received %s", response[4:])
    return False


def verify_negative_response(response, nrc_code):
    """
    Verify security access request seed negative response
    Args:
        dut (Dut): An instance of Dut
        nrc_code(str): UDS negative response code
    Returns: True when negative response successfully verified
    """
    # Extract and compare with NRC code
    if response[6:8] == nrc_code:
        logging.info("NRC %s received as expected", response[6:8])
        return True

    logging.error("Expected negative response %s, received %s", nrc_code, response[6:8])
    return False


def compare_time(elapsed_time, parameters, time_flag=False):
    """
    Verify elapsed time is within server maximum response time
    Args:
        elapsed_time (float): elapsed time of clientRequestSeed
        parameters(dict): Maximum response time (5000ms)
        time_flag(bool): True to calculate upper boundary time (7s)
    Returns: True when successfully verified
    """
    result = False
    if time_flag:
        # Calculate wait time and wait for next request
        if elapsed_time < parameters['sa_response_time']:
            wait_time = parameters['sa_response_time'] - elapsed_time
            time.sleep(wait_time)
            elapsed_time = elapsed_time + wait_time

        boundary_time = parameters['sa_response_time'] + parameters['time_range']
        # Check the boundary value between 5 and 7 second of server timer start
        if elapsed_time >= parameters['sa_response_time']:
            if elapsed_time <= boundary_time:
                logging.info("Elapsed time %ss is within %ss and %ss", elapsed_time,
                             parameters['sa_response_time'], boundary_time)
                result = True
            else:
                logging.error("Elapsed time %ss is not within time %ss and time %ss",
                            elapsed_time, parameters['sa_response_time'], boundary_time)
                result = False
    else:
        boundary_time = parameters['sa_response_time'] - parameters['time_range']
        # Calculate wait time and wait for next request
        if elapsed_time < boundary_time:
            wait_time = boundary_time - elapsed_time
            time.sleep(wait_time)
            elapsed_time = elapsed_time + wait_time

        # Check the boundary value between 3 and 5 second of server timer start
        if elapsed_time >= boundary_time:
            if elapsed_time <= parameters['sa_response_time']:
                logging.info("Elapsed time %ss is within %ss and %ss", elapsed_time,
                             boundary_time, parameters['sa_response_time'])
                result = True
            else:
                logging.error("Elapsed time %ss is not within time %ss and time %ss",
                            elapsed_time, boundary_time, parameters['sa_response_time'])
                result = False

    return result


def step_1(dut: Dut):
    """
    action: Verify maximum of two clientRequestSeed are accepted within time of 5000ms
    expected_result: positive response on successful verification of only two
                     clientRequestSeed requests accepted within time of 5000ms
    """
    # Read yml parameters
    parameters_dict = {'sa_response_time': 0,
                       'time_range': 0}
    parameters = SIO.parameter_adopt_teststep(parameters_dict)
    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False, None, None

    # Set to programming session
    dut.uds.set_mode(2)

    # 1st clientRequestSeed for positive response
    response = security_access_request_seed(dut, subfunction_flag=False)

    # Capture start time of clientRequestSeed
    start_time = float(SC.can_frames[dut['send']][0][0])
    result = verify_positive_response(response)
    if result:
        # 2nd clientRequestSeed for positive response
        response = security_access_request_seed(dut, subfunction_flag=False)
        result = verify_positive_response(response)

    # Capture end time of clientRequestSeed after 2nd request
    end_time = float(SC.can_frames[dut['receive']][0][0])
    # Elapsed time for first 2 requests
    elapsed_time = end_time - start_time

    # Calculate and verify elapsed time is within 3s and 5s
    result = result and compare_time(elapsed_time, parameters, time_flag=False)

    if result:
        # 3rd clientRequestSeed for negative response
        response = security_access_request_seed(dut, subfunction_flag=False)
        # Verify NRC 22 (conditionNotCorrect)
        result = verify_negative_response(response, nrc_code='22')

    # Capture end time of clientRequestSeed after 3rd request
    end_time = float(SC.can_frames[dut['receive']][0][0])

    # Calculate elapsed time
    elapsed_time = end_time - start_time
    # Calculate and verify elapsed time is still within 5s after 3rd request
    result = result and compare_time(elapsed_time, parameters, time_flag=False)

    if result:
        logging.info("Two clientRequestSeed accepted within valid time of 5000ms and"
                     " third request is rejected as expected")
        return True, parameters, start_time

    logging.error("Test failed: Two clientRequestSeed not accepted within valid time of 5000ms")
    return False, None, None


def step_2(dut: Dut, parameters, start_time):
    """
    action: Verify valid clientSendKey is received to reset server timer
    expected_result: Positive response on successful verification of server key response
    """
    # Reset security access ongoing timer
    end_time = time.time()
    # Calculate elapsed time
    elapsed_time = end_time - start_time

    # Calculate and verify elapsed time is within 5s and 7s
    result = compare_time(elapsed_time, parameters, time_flag=True)
    if result:
        result = SE27.activate_security_access_fixedkey(dut, sa_keys=CNF.default_rig_config,
                                                step_no=272, purpose="SecurityAccess")
    if result:
        logging.info("Valid clientSend key is received to reset ongoing server timer")
        return True

    logging.error("Test Failed: Security access requested with invalid ClientSend key "
                  "or invalid response")
    return False


def step_3(dut: Dut, parameters):
    """
    action: Verify acceptance of two clientRequestSeed after timer reset and ClientRequestSeed
            response received with invalid subfunction
    expected_result: Positive response on successful verification of two clientRequestSeed
                     requests accepted after timer reset and ClientRequestSeed response received
                     with invalid subfunction
    """

    # 1st clientRequestSeed for negative response
    response = security_access_request_seed(dut, subfunction_flag=True)

    # Capture start time of 1st clientRequestSeed
    start_time = float(SC.can_frames[dut['send']][0][0])

    # Verify NRC 12 (subFunctionNotSupported)
    result = verify_negative_response(response, nrc_code='12')
    if result:
        # 2nd clientRequestSeed for positive response
        response = security_access_request_seed(dut, subfunction_flag=False)
        result = verify_positive_response(response)

    if result:
        # 3rd clientRequestSeed for positive response
        response = security_access_request_seed(dut, subfunction_flag=False)
        result = verify_positive_response(response)

    # Capture end time of clientRequestSeed after 3rd request
    end_time = float(SC.can_frames[dut['receive']][0][0])

    # Calculate elapsed time in milliseconds
    elapsed_time = end_time - start_time
    # Verify elapsed time is within 5000ms
    if result and elapsed_time <= parameters['sa_response_time']:
        logging.info("Two clientRequestSeed accepted after timer reset and request"
                     "with invalid subfunction is rejected within valid 5000ms")
        return True
    logging.error("Test Failed: Two clientRequestSeed not accepted within valid time of "
                  "5000ms or subfunction not rejected")
    return False


def run():
    """
    Verify two consecutive clientRequestSeed are accepted within valid time of 5000ms and
    with valid subfunction
    """

    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=60)
        result_step, parameters, sa_start_time = dut.step(step_1, purpose="Verify number of"
                                          " clientRequestSeed accepted within timeout")
        if result_step:
            result_step = dut.step(step_2, parameters, sa_start_time, purpose="Verify valid"
                                   " clientSendKey is received to reset server timer")
        if result_step:
            result_step = dut.step(step_3, parameters, purpose="Verify number of clientRequestSeed"
                                   " received with valid and invalid subfunction")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
