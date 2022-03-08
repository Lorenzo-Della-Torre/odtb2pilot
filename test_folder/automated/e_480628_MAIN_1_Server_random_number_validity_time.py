"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.


NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/


reqprod: 480628
version: 1
title: Server random_number validity time

purpose: >
    To reduce the possibilities for e.g. off board computations to identify a valid response.
    The expected maximum system delay in a vehicle is known.

description: >
    The active server random number (active seed) provided in serverResponseSeed message
    shall maximum be valid for 5000ms, i.e. the maximum time between serverResponseSeed and
    clientSendKey (server timer) must be less or equal to 5000ms. A clientSendKey received when
    that timer is expired must be rejected and the sequence is required to be restarted by a
    new clientRequestSeed and all random numbers shall be newly generated (fresh).
    Notes-
    Server might be unlocked while last client timer is expired.
    At the client side, the request/response validity time shall be according to the P4Server_max
    response time for the securityAccess service.

details: > Validate Security Access response based on given Server random number
    validity time, with positive and negative response received by server.
    Steps-
    1. set to programming session mode and Security Access to ECU and return response
    2. Verify if response is valid when Server random number valid time is 5000ms
    3. Verify invalid response (0x7F) and unique Server random number for invalid time of 5100ms
"""

import logging
import time
from hilding.dut import DutTestError
from hilding.dut import Dut
from hilding.conf import Conf
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_can import SupportCAN

SSA = SupportSecurityAccess()
SC = SupportCAN()
CNF = Conf()


def security_access_method(dut: Dut, timer):
    """
    Security Access to ECU and store response of sub functions
    Args:
        dut (class obj): Dut instance
        timer(bool): flag to set delay of 5100ms for invalid Server random number time
    Returns:
        response_dict(dict): security access message response
    """

    response_dict = {'response_id': '', 'response_code': '',
                     'iv': '', 'time_elapsed': ''}
    time_elapsed = 0
    dut.uds.set_mode(2)
    SSA.set_keys(CNF.default_rig_config)
    SSA.set_level_key(1)

    # prepare request for a “client request seed”
    payload = SSA.prepare_client_request_seed()
    response = dut.uds.generic_ecu_call(payload)
    payload = response.raw[4:]

    # Initialization vector start and end index
    # For clientRequestSeed 12:44
    response_dict['iv'] = response.raw[12:44]
    SSA.process_server_response_seed(bytearray.fromhex(payload))
    payload = SSA.prepare_client_send_key()

    if timer:
        # set delay of 5100ms to get invalid response
        time.sleep(5.1)
    t_sent = float(SC.can_frames[dut['send']][0][0])
    response = dut.uds.generic_ecu_call(payload)
    t_received = float(SC.can_frames[dut['receive']][0][0])
    # time taken for clientsendkey response
    time_elapsed = int((t_received - t_sent) * 1000)

    # Response Id start and end index 2:4
    response_dict['response_id'] = response.raw[2:4]
    # Response code start and end index 6:8
    response_dict['response_code'] = response.raw[6:8]
    response_dict['time_elapsed'] = time_elapsed
    return response_dict


def step_1(dut: Dut):
    """
    action: Verify if response is valid when Server random number valid time is 5000ms
    expected_result: True on successfully verified valid response in valid time of 5000ms
    """

    timer = False
    response_dict = security_access_method(dut, timer)
    if response_dict is not None:
        if response_dict['response_id'] == '67':
            return True
    logging.error("Test failed: Invalid response for Server random number validity time of 5000ms")
    return False


def step_2(dut: Dut, timer):
    """
    action: Verify invalid response and unique Server random number when validity time is 5100ms
    expected_result: True on successfully verified invalid response (0x7F) and unique Server random
                     number in time of 5100ms
    """

    timer = True
    # max response time (P4Server_max) for programming session is 2500ms
    # (shall be equal to "P2Server_max")
    p4server_max = 2500
    response_dict = security_access_method(dut, timer)

    if response_dict is None:
        logging.error("Test failed: Invalid response")
        return False
    server_random_no = response_dict['iv']

    # verify for Negative response serviceNotSupported (0x7F) and
    # conditionsNotCorrect (0x22) response code
    if response_dict['response_id'] == '7F' and response_dict['response_code'] == '22':
        timer = False
        # prepare new request for client request seed and check unique Server random number
        response_dict = security_access_method(dut, timer)
        if server_random_no != response_dict['iv'] and response_dict['time_elapsed'] <= \
                p4server_max:
            return True

    logging.error("Test failed: Verification of invalid response (0x7F) and unique Server"
                  " random number failed in validity time of 5100ms")
    return False


def run():
    """
    Verify valid response and Server random number based on validity time,
    with positive and negative response received.
    """

    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False
    timer = False

    try:
        dut.precondition()
        result_step = dut.step(step_1, purpose="Verify valid response when Server random"
                               " number time is 5000ms")
        if result_step:
            result = dut.step(step_2, timer, purpose="Verify invalid response and unique Server"
                              " random number when validity time is 5100ms")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
