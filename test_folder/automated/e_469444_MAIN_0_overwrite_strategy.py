"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 469444
version: 0
title: Overwrite strategy
purpose: >
    To reduce the risk of data being erased

description: >
    The log data must be protected from being erased.
    The default overwrite strategy to be applied is First-In-First-Out (FIFO),
    i.e. time-based. If there is some critical event that shall be excluded from
    this policy, this must be explicitly specified elsewhere.
    FIFO shall apply for every type, meaning that an event categorized as one type
    shall not overwrite an older event for a second type. For an event type where
    half of the events are dedicated for successful- and the other half for rejected
    attempts, there will be two separate FIFO lists

details: >
    Verify overwrite strategy to reduce the risk of data being erased
"""

import logging
import time
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_service27 import SupportService27
import supportfunctions.support_service27 as SP27

SE27 = SupportService27()


def get_successful_rejected_events_and_codes(response):
    """
    Extract event data from ECU response
    Args:
        response (dict): ECU response
    Returns:
        events_and_codes (dict): Security event data for successful and rejected event
    """
    events_and_codes = {'total_successful_events': '',
                        'latest_successful_event_code': '',
                        'total_rejected_events': '',
                        'latest_rejected_event_code': ''}

    response_items = response.data['details']['response_items']
    events_and_codes['total_successful_events'] = int(response_items[0]['sub_payload'], 16)
    events_and_codes['latest_successful_event_code'] = response_items[2]['sub_payload']
    events_and_codes['total_rejected_events'] = int(response_items[1]['sub_payload'], 16)

    for response_item in response_items:
        if response_item['name'] == "Latest rejected event - Event Code":
            events_and_codes['latest_rejected_event_code'] = response_item['sub_payload']
            break

    return events_and_codes


def security_access_with_invalid_key(dut):
    """
    Security access with invalid key
    Args:
        dut (Dut): An instance of Dut
    Returns:
        (bool): True if security access denied for invalid key
    """
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
        return True

    return False


def step_1(dut: Dut):
    """
    action: Read security log event DID D046 and extract event data
    expected_result: True when event data are extracted successfully
    """
    # Set ECU in extended session
    dut.uds.set_mode(3)

    response = dut.uds.read_data_by_id_22(bytes.fromhex('D046'))
    if response.raw[4:6] == '62':
        events_and_codes = get_successful_rejected_events_and_codes(response)
        logging.info("Successfully extracted security log event data")
        return True, events_and_codes

    logging.error("Test Failed: Expected positive response '62', received %s", response.raw)
    return False, None


def step_2(dut: Dut):
    """
    action: Security access with valid key for 15 times
    expected_result: True when security access is successful for all attempts
    """
    results = []

    # Set ECU in default session
    dut.uds.set_mode(1)

    for _ in range(15):
        dut.uds.set_mode(2)
        result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config)
        results.append(result)
        time.sleep(2)

    if len(results) != 0 and all(results):
        logging.info("Security access is successful for all attempts")
        return True

    logging.error("Test Failed: Security access denied in programming session")
    return False


def step_3(dut: Dut, events_and_codes):
    """
    action: Verify security log event data for successful event
    expected_result: True when total number of successful events is incremented by 15 and Latest
                     successful event code is '80'
    """
    # Set ECU in extended session
    dut.uds.set_mode(1)
    dut.uds.set_mode(3)
    time.sleep(2)

    response = dut.uds.read_data_by_id_22(bytes.fromhex('D046'))
    latest_events_and_codes = get_successful_rejected_events_and_codes(response)

    total_successful_events_latest = latest_events_and_codes['total_successful_events']
    total_successful_events = events_and_codes['total_successful_events']
    latest_successful_event_code = latest_events_and_codes['latest_successful_event_code']

    if total_successful_events_latest == total_successful_events + 15:
        if latest_successful_event_code == '80':
            logging.info("Received security event data for successful event as expected")
            return True

    logging.error("Test Failed: Event count is not increased or event code is wrong for successful"
                  " event")
    return False


def step_4(dut: Dut):
    """
    action: Security access with invalid key for 16 times
    expected_result: True when security access is denied for all attempts
    """
    results = []

    # Set ECU in default session
    dut.uds.set_mode(1)

    for count in range(16):
        dut.uds.set_mode(2)
        result = security_access_with_invalid_key(dut)
        results.append(result)
        if count % 2 != 0:
            time.sleep(10)

    if len(results) != 0 and all(results):
        logging.info("Security access is denied for invalid key for all attempt as expected")
        return True

    logging.error("Test Failed: Security access is not denied for invalid key")
    return False


def step_5(dut: Dut, events_and_codes):
    """
    action: Verify security log event data for rejected event
    expected_result: True when total number of rejected events is incremented by 16 and latest
                     rejected event code is '02'
    """
    # Set ECU in extended session
    dut.uds.set_mode(1)
    dut.uds.set_mode(3)
    time.sleep(2)

    response = dut.uds.read_data_by_id_22(bytes.fromhex('D046'))
    latest_events_and_codes = get_successful_rejected_events_and_codes(response)

    total_rejected_events_latest = latest_events_and_codes['total_rejected_events']
    total_rejected_events = events_and_codes['total_rejected_events']
    latest_rejected_event_code = latest_events_and_codes['latest_rejected_event_code']

    if total_rejected_events_latest == total_rejected_events + 16:
        if latest_rejected_event_code == '02':
            logging.info("Received security event data for rejected event as expected")
            return True, latest_events_and_codes

    logging.error("Test Failed: Rejected event count is not increased or event code is wrong")
    return False, None


def step_6(dut: Dut):
    """
    action: Security access in programming session
    expected_result: True when security access successful in programming session
    """
    # Set ECU in programming session
    dut.uds.set_mode(2)
    time.sleep(2)

    result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config)
    if result:
        logging.info("Security access is successful in programming session")
        return True

    logging.error("Test Failed: Security access is denied in programming session")
    return False


def step_7(dut: Dut, events_and_codes):
    """
    action: Verify successful events are incremented by one and rejected events are unchanged
    expected_result: True when successful events are incremented by one and rejected events are
                     unchanged
    """
    # Set ECU in extended session
    dut.uds.set_mode(1)
    dut.uds.set_mode(3)
    time.sleep(2)

    response = dut.uds.read_data_by_id_22(bytes.fromhex('D046'))
    latest_events_and_codes = get_successful_rejected_events_and_codes(response)

    total_rejected_events_latest = latest_events_and_codes['total_rejected_events']
    total_rejected_events = events_and_codes['total_rejected_events']
    total_successful_events_latest = latest_events_and_codes['total_successful_events']
    total_successful_events = events_and_codes['total_successful_events']

    if total_rejected_events_latest == total_rejected_events:
        if total_successful_events_latest == total_successful_events + 1:
            logging.info("Successful events are incremented by one and rejected events are "
                         "unchanged as expected")
            return True, latest_events_and_codes

    logging.error("Test Failed: Successful events are not incremented or rejected events are "
                  "changed")
    return False, None


def step_8(dut: Dut):
    """
    action: Security access with invalid key
    expected_result: True when security access denied for invalid key
    """
    # Set ECU in programming session
    dut.uds.set_mode(2)
    time.sleep(2)

    result = security_access_with_invalid_key(dut)
    if result:
        logging.info("Security access denied for invalid key as expected")
        return True

    logging.error("Test Failed: Security access is not denied for invalid key")
    return False


def step_9(dut: Dut, events_and_codes):
    """
    action: Verify security log event data after security access with invalid key
    expected_result: True when rejected events and codes are overwritten but successful events are
                     unchanged
    """
    # Set ECU in extended session
    dut.uds.set_mode(1)
    dut.uds.set_mode(3)
    time.sleep(2)

    response = dut.uds.read_data_by_id_22(bytes.fromhex('D046'))

    latest_rej_event_code_index = int(len(response.data['details']['response_items'])/2 + 1)
    latest_events_and_codes = get_successful_rejected_events_and_codes(response)
    event_code_latest = \
        response.data['details']['response_items'][latest_rej_event_code_index]['sub_payload']

    total_rejected_events_latest = latest_events_and_codes['total_rejected_events']
    total_rejected_events = events_and_codes['total_rejected_events']
    total_successful_events_latest = latest_events_and_codes['total_successful_events']
    total_successful_events = events_and_codes['total_successful_events']
    latest_rejected_event_code = events_and_codes['latest_rejected_event_code']

    if total_rejected_events_latest == total_rejected_events + 1:
        if total_successful_events_latest == total_successful_events:
            if event_code_latest == '01' and latest_rejected_event_code == '02':
                logging.info("Rejected events and codes are overwritten but successful events are "
                             "unchanged as expected")
                return True

    logging.error("Test Failed: Rejected events and codes are not overwritten or successful events"
                  " are changed")
    return False


def run():
    """
    Verify overwrite strategy to reduce the risk of data being erased
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=400)
        result_step, events_and_codes = dut.step(step_1, purpose="Read security log event DID D046"
                                                                 " and extract event data")
        if result_step:
            result_step = dut.step(step_2, purpose="Security access with valid key for 15 times")
        if result_step:
            result_step = dut.step(step_3, events_and_codes, purpose="Verify security log event "
                                                                     "data for successful event")
        if result_step:
            result_step = dut.step(step_4, purpose="Security access with invalid key for 16 times")
        if result_step:
            result_step, events_and_codes = dut.step(step_5, events_and_codes,purpose="Verify "
                                                     "security log event data for rejected event")
        if result_step:
            result_step = dut.step(step_6, purpose="Security access in programming session")
        if result_step:
            result_step, events_and_codes = dut.step(step_7, events_and_codes, purpose="Verify "
                                                     "successful events incremented by one and "
                                                     "rejected events is unchanged")
        if result_step:
            result_step = dut.step(step_8, purpose="Security access to ECU with invalid key")
        if result_step:
            result_step = dut.step(step_9, events_and_codes, purpose="Verify security log event "
                                                             "data for rejected event")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
