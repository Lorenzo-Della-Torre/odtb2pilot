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

details: >
    Validate Security Access response based on given 'server random number validity time', with
    positive and negative response received by server.
    Steps-
    1. Set to programming session mode and Security Access to ECU and return response
    2. Verify if response is valid when Server random number valid time is 5000ms
    3. Verify invalid response (0x7F) and unique Server random number for invalid time of 5100ms
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_sec_acc import SupportSecurityAccess

SC = SupportCAN()
SSA = SupportSecurityAccess()


def security_access_method(dut, timer):
    """
    Security access to ECU and store response of sub functions
    Args:
        dut (Dut): An instance of Dut
        timer (bool): Flag to set delay of 5100ms
    Returns:
        response_dict (dict): Security access message response
    """
    # Set ECU to programming session
    dut.uds.set_mode(2)

    # Time sleep to avoid NRC-37
    time.sleep(5)

    response_dict = {'response_id': '', 'response_code': '',
                     'initialization_vector': '', 'time_elapsed': ''}

    SSA.set_keys(sa_keys=dut.conf.default_rig_config)
    SSA.set_level_key(int('01', 16))
    payload = SSA.prepare_client_request_seed()

    response = dut.uds.generic_ecu_call(payload)
    payload = response.raw[4:]
    response_dict['initialization_vector'] = response.raw[12:44]
    SSA.process_server_response_seed(bytearray.fromhex(payload))
    payload = SSA.prepare_client_send_key()
    if timer:
        # set delay of 5100ms to get invalid response
        time.sleep(5.1)

    t_sent = float(SC.can_frames[dut['send']][0][0])
    response = dut.uds.generic_ecu_call(payload)
    t_received = float(SC.can_frames[dut['receive']][0][0])
    response_dict['time_elapsed'] = int((t_received - t_sent) * 1000)

    SSA.process_server_response_key(bytearray.fromhex(response.raw[6:(6+4)]))
    response_dict['response_id'] = response.raw[2:4]
    response_dict['response_code'] = response.raw[6:8]

    return response_dict


def step_1(dut: Dut):
    """
    action: Verify response for 'server random number validity time' within 5000ms
    expected_result: ECU should give positive response for 'server random number validity time'
                     within 5000ms
    """
    response_dict = security_access_method(dut, timer=False)
    if response_dict['response_id'] == '67':
        logging.info("Received positive response for 'server random number validity time' within "
                     "5000ms as expected")
        return True

    logging.error("Test Failed: Invalid response for 'server random number validity time' within "
                  "5000ms")
    return False


def step_2(dut: Dut):
    """
    action: Verify response for 'server random number validity time' is 5100ms and also verify
            unique server random number for 5100ms
    expected_result: ECU should give negative response and unique server random number for 5100ms
    """
    p4server_max = 2500

    # Security access for 'server random number validity time' 5100ms
    response_dict = security_access_method(dut, timer=True)
    server_random_no = response_dict['initialization_vector']

    if response_dict['response_id'] == '7F' and response_dict['response_code'] == '22':
        response_dict = security_access_method(dut, timer=False)

        if server_random_no != response_dict['initialization_vector'] and \
        response_dict['time_elapsed'] <= p4server_max:
            logging.info("Received negative response and unique server random number for 5100ms "
                         "as expected")
            return True

    logging.error("Test Failed: Negative response '7F' is not received or unique server random "
                  "number is incorrect")
    return False


def run():
    """
    Verify response for 'server random number validity time' more and less than maximum value
    (5000ms) also verify unique server random number for 5100ms
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=90)

        result_step = dut.step(step_1, purpose="Verify positive response for server random number "
                                               "validity time within 5000ms")
        if result_step:
            result = dut.step(step_2, purpose="Verify negative response and unique server random "
                                              "number when validity time is 5100ms")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
