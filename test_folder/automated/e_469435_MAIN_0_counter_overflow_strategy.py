"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 469435
version: 0
title: Counter overflow strategy
purpose:
    Define the strategy if the counter(s) defined in the SecurityEventHeader overflows.
    By defining a counter of a appropriate length, the risk of counter overflow between
    two readouts is reduced.

description:
    The counters defined in the SecurityEvent Header shall have a length of at least 4 bytes.
    Counter overflow is accepted but there shall be no possibility to reset the counters.

details:
    Verify counter overflow strategy
    Steps:
        1. Read security log event DID 'D046'
        2. Set ECU in programming session and verify active diagnostic session
        3. Security access to ECU in programming session
        4. Set ECU to default session and read security log event DID 'D046'
        5. Security access to ECU in programming session with invalid key
        6. ECU reset
        7. Set ECU to default session and read security log event DID 'D046'
"""

import logging
import time
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_service27 import SupportService27
import supportfunctions.support_service27 as SP27

SE27 = SupportService27()


def get_total_events(response):
    """
    Get total number of of events
    Args:
        response (dict): ECU response
    Returns:
        total_events (dict): Dict of total successful and rejected events
    """
    total_events = {'total_successful_event': 0,
                    'total_rejected_event': 0}

    for response_item in response.data['details']['response_items']:
        if response_item['name'] == "Total number of successful events":
            total_events['total_successful_event'] = int(response_item['sub_payload'], 16)

        if response_item['name'] == "Total number of rejected events":
            total_events['total_rejected_event'] = int(response_item['sub_payload'], 16)

        if total_events['total_successful_event'] != 0 and \
                total_events['total_rejected_event'] != 0:
            break

    return total_events


def get_latest_events_code(response):
    """
    Get latest events codes
    Args:
        response (dict): ECU response
    Returns:
        latest_events_code (dict): Dict of latest successful and rejected events code
    """
    latest_events_code = {'latest_successful_event_code': '',
                          'latest_rejected_event_code': ''}

    for response_item in response.data['details']['response_items']:
        if response_item['name'] == "Latest successful event - Event Code":
            latest_events_code['latest_successful_event_code'] = \
            response_item['sub_payload']

        if response_item['name'] == "Latest rejected event - Event Code":
            latest_events_code['latest_rejected_event_code'] = \
            response_item['sub_payload']

        if latest_events_code['latest_successful_event_code'] != '' and \
            latest_events_code['latest_rejected_event_code'] != '':
            break

    return latest_events_code


def step_1(dut: Dut):
    """
    action: Read security log event DID 'D046'
    expected_result: Positive response '62' with the event data
    """
    response = dut.uds.read_data_by_id_22(bytes.fromhex('D046'))
    total_events = get_total_events(response)
    if response.raw[4:6] == '62':
        logging.info("Received positive response '62' for ReadDataByIdentifier as expected")
        return True, total_events

    logging.info("Test Failed: Expected positive response '62' for ReadDataByIdentifier, but "
                 "received %s", response.raw)
    return False, None


def step_2(dut: Dut):
    """
    action: Set ECU in programming session and verify active diagnostic session
    expected_result: True when ECU is in programming session
    """
    # Set to programming session
    dut.uds.set_mode(2)

    res = dut.uds.active_diag_session_f186()
    result = bool(res.data['sid'] == '62' and res.data['details']['mode'] == 2)
    if result:
        logging.info("ECU is in programming session as expected")
        return True

    logging.error("Test Failed: ECU is not in programming session, received mode %s",
                  res.data['details']['mode'])
    return False


def step_3(dut: Dut):
    """
    action: Security access to ECU in programming session
    expected_result: True when security access successful in programming session
    """
    # Sleep time to avoid NRC37
    time.sleep(5)
    sa_result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config,
                                                       step_no=272, purpose="SecurityAccess")
    if sa_result:
        logging.info("Security access successful in programming session")
        return True

    logging.error("Test Failed: Security access denied in programming session")
    return False


def step_4(dut: Dut, total_events):
    """
    action: Set ECU to default session and read security log event DID 'D046'
    expected_result: True when total number of successful event incremented by 1 and
                     Latest successful event code is '80'
    """
    # Set to default session
    dut.uds.set_mode(1)

    time.sleep(2)
    response = dut.uds.read_data_by_id_22(bytes.fromhex('D046'))
    total_events_latest = get_total_events(response)
    events_code_latest = get_latest_events_code(response)

    if total_events_latest['total_successful_event'] == total_events['total_successful_event'] + 1\
        and events_code_latest['latest_successful_event_code'] == '80':
        logging.info("Received security event data for successful event as expected")
        return True

    logging.error("Test Failed: Successful event count is not increased or the event code "
                  "is wrong")
    return False


def step_5(dut: Dut):
    """
    action: Security access to ECU in programming session with invalid key
    expected_result: True when security access denied in programming session
    """
    # Set to programming session
    dut.uds.set_mode(2)

    sa_keys = dut.conf.default_rig_config
    result, payload = SE27.activate_security_access_seed_and_calc(dut, sa_keys)
    if not result:
        logging.error("Request seed failed for security access")
        return False

    # Corrupting key payload
    payload[4] = 0xFF
    payload[5] = 0xFF

    # Security access with invalid key
    result, response = SE27.security_access_send_key(dut, sa_keys, payload)
    result = result and SP27.SSA.process_server_response_key(bytearray.fromhex(response))

    if not result:
        logging.info("Security access denied in programming session")
        return True

    logging.error("Test Failed: Security access is successful for invalid key")
    return False


def step_6(dut: Dut):
    """
    action: ECU reset
    expected_result: Positive response '51'
    """
    response = dut.uds.ecu_reset_1101()
    result = bool(response.data['sid'] == '51')
    if result:
        logging.info("ECU reset successful")
        return True

    logging.error("Test Failed: ECU reset failed")
    return False


def step_7(dut: Dut, total_events):
    """
    action: Set ECU to default session and read security log event DID 'D046'
    expected_result: True when DID D046 event counters are same as before ECU reset and
                     total number of successful and rejected events is incremented by 1 and
                     latest successful event code is '80' and rejected event code is '01'
    """
    # Set to default session
    dut.uds.set_mode(1)

    time.sleep(3)
    response = dut.uds.read_data_by_id_22(bytes.fromhex('D046'))
    total_events_latest = get_total_events(response)
    events_code_latest = get_latest_events_code(response)

    if total_events_latest['total_successful_event'] == total_events['total_successful_event'] + 1\
        and events_code_latest['latest_successful_event_code'] == '80':
        logging.info("Received security event data for successful event as expected")

        if total_events_latest['total_rejected_event'] == total_events['total_rejected_event'] + 1\
            and events_code_latest['latest_rejected_event_code'] == '01':
            logging.info("Received security event data for rejected event as expected")
            return True

        logging.error("Test Failed: Rejected event count is not increased or the event code "
                      "is wrong")
        return False

    logging.error("Test Failed: Successful event count is not increased or the event code "
                  "is wrong")
    return False


def run():
    """
    Verify counter overflow strategy
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(90)
        result_step, total_events = dut.step(step_1, purpose='Read security log event DID D046')
        if result_step:
            result_step = dut.step(step_2, purpose='Set ECU in programming session and verify '
                                                   'active diagnostic session')
        if result_step:
            result_step = dut.step(step_3, purpose='Security access to ECU in programming session '
                                                   'with Valid Key')
        if result_step:
            result_step = dut.step(step_4, total_events, purpose='Set ECU to default session and '
                                                         'read security log event DID D046')
        if result_step:
            result_step = dut.step(step_5, purpose='Security access to ECU in programming session '
                                                   'with invalid key')
        if result_step:
            result_step = dut.step(step_6, purpose='ECU reset')
        if result_step:
            result_step = dut.step(step_7, total_events, purpose='Set ECU to default session and '
                                                         'read security log event DID D046')
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
