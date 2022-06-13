"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 469433
version: 0
title: Total number of events
purpose: >
    Define content of a security event header.

description: >
    The ECU record the total number of events reported for each event type
    (TotalNumberOfReportedEvents). For some event types, it's important
    to be able to distinguish between successful- and rejected attempts.
    Hence, the Security Event Header could optionally include a second counter.

    For each event type, one of the two following Security Event Header counter
    structures shall be used;

        Security Event Header type 1, including one single counter of all reported
        events (TotalNumberOfReportedEvents).

        Security Event Header type 2, including two counters;
        the first counter keep track of the successful attempts (TotalNumberOfSuccessfulEvents)
        and the second attempt counts the number of rejected attempts
        (TotalNumberOfRejectedEvents). This is to be applied when successful and
        rejected attempts are reported and could be separated

    Example.
    Event Type is for Software Update. Security Event Header Type 2 is used, as it is
    relevant to store history about both successful and failed events.
        Counter 1: Counts the number of successful software updates.
        Counter 2: Counts the number of rejected (but started) software updates.

details: >
    Read Security log event DID D046 and record the total number of
    successful and rejected events.
    Unlock the Security Access and check the Security Access is successful by
    incrementing successful event 1.
    Send invalid security access key to get the rejected software update(events)
    and check the rejected event count is increased by 1 and software update is rejected.

"""

import logging
import time
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_file_io import SupportFileIO
from hilding.dut import Dut
from hilding.dut import DutTestError
import supportfunctions.support_service27 as SP27

SIO = SupportFileIO()
SE27 = SupportService27()


def get_successful_rejected_events_and_codes(response):
    """
    expected result: return dict of total successful, rejected events and codes
    """
    events_and_codes = {
                        'total_successful_events': '',
                        'latest_successful_event_code': '',
                        'total_rejected_events': '',
                        'latest_rejected_event_code': ''
                        }
    for response_item in response.data['details']['response_items']:
        if response_item['name'] == "Total number of successful events":
            events_and_codes['total_successful_events'] = int(
                response_item['sub_payload'], 16)
        if response_item['name'] == "Latest successful event - Event Code":
            events_and_codes['latest_successful_event_code'] = \
                response_item['sub_payload']
        if response_item['name'] == "Total number of rejected events":
            events_and_codes['total_rejected_events'] = int(
                response_item['sub_payload'], 16)
        if response_item['name'] == "Latest rejected event - Event Code":
            events_and_codes['latest_rejected_event_code'] = \
                response_item['sub_payload']
        if events_and_codes['total_successful_events'] != '' and \
            events_and_codes['latest_successful_event_code'] != '' and \
            events_and_codes['total_rejected_events'] != '' and \
            events_and_codes['latest_rejected_event_code'] != '':
            break
    return events_and_codes


def step_1(dut: Dut):
    """
    action: Read Security log event DID D046
    expected_result: Positive response with the event data

    total_events: return dictionary of successful and rejected event count
    """
    response = dut.uds.read_data_by_id_22(b'\xd0\x46')
    # NRC 31 requestOutOfRange
    if response.raw[6:8] != '31':
        events_and_codes = \
            get_successful_rejected_events_and_codes(response)
    if response.raw[4:6] == '62':
        return True, events_and_codes
    return False, None


def step_2(dut: Dut):
    """
    action: Set ECU to Programming Session
    expected_result: Positive response
    """
    dut.uds.set_mode(2)
    res = dut.uds.active_diag_session_f186()
    if res.data['sid'] == '62' and res.data['details']['mode'] == 2:
        return True
    return False


def step_3(dut: Dut):
    """
    action: Security Access to ECU
    expected_result: Positive response
    """

    result = SE27.activate_security_access_fixedkey(dut,
                                                    dut.conf.default_rig_config, step_no=3,
                                                    purpose="Security Access"
                                                    )
    return result


def step_4(dut: Dut, events_and_codes):
    """
    action: Set ECU to Default session and
            Read Security log event DID D046
    expected_result: Total number of successful events is incremented by 1
                     Latest successful event code is '80'
    """
    dut.uds.set_mode()
    result = False
    time.sleep(2)
    response = dut.uds.read_data_by_id_22(b'\xd0\x46')
    latest_events_and_codes = \
        get_successful_rejected_events_and_codes(response)
    if events_and_codes['total_successful_events'] + 1 == \
        latest_events_and_codes['total_successful_events'] and \
        latest_events_and_codes['latest_successful_event_code'] == '80':
        result = True
    else:
        logging.error("Successful event not increased or unknown event code")
        result = False
    return result

def step_5(dut: Dut):
    """
    action: Set ECU to Programming Session
    expected_result: Positive response
    """
    dut.uds.set_mode(2)
    res = dut.uds.active_diag_session_f186()
    if res.data['sid'] == '62' and res.data['details']['mode'] == 2:
        return True
    return False


def step_6(dut: Dut):
    """
    action: Security Access to ECU for rejected event
    expected_result: Negative response
    """
    sa_keys = dut.conf.default_rig_config

    SP27.SSA.set_keys(sa_keys)
    result, response = SE27.security_access_request_seed(dut, sa_keys)
    SP27.SSA.process_server_response_seed(
        bytearray.fromhex(response))
    payload = SP27.SSA.prepare_client_send_key()
    payload[4] = 0xFF
    payload[5] = 0xFF
    result, response = SE27.security_access_send_key(dut, sa_keys, payload)
    result = (SP27.SSA.process_server_response_key(bytearray.fromhex(response)) == 0)
    if result:
        return False

    logging.info("Received Negative response for a wrong key as expected")
    return True


def step_7(dut: Dut, events_and_codes):
    """
    action: Set ECU to Default session and
            Read Security log event DID D046
    expected_result: Total number of Rejected events is incremented by 1
                     Latest rejected event code is '01'
    """
    dut.uds.set_mode()
    time.sleep(2)
    result = False
    response = dut.uds.read_data_by_id_22(b'\xd0\x46')
    latest_events_and_codes = \
        get_successful_rejected_events_and_codes(response)
    if events_and_codes['total_rejected_events'] + 1 == \
        latest_events_and_codes['total_rejected_events'] and \
            latest_events_and_codes['latest_rejected_event_code'] == "01":
        result = True
    else:
        logging.error("Rejected event not increased or unknown event code")
        result = False
    return result


def run():
    """ Supporting functional requests """
    dut = Dut()
    start_time = dut.start()
    result = False
    try:
        dut.precondition()
        result, events_and_codes = dut.step(step_1, purpose='Read DID D046')
        result = result and dut.step(step_2, purpose='ECU into programming session')
        result = result and dut.step(step_3, purpose='Security Access')
        result = result and dut.step(step_4, events_and_codes,
                           purpose='ECU to Default session and Read and compare\
                               total_succ_events and event code')
        result = result and dut.step(step_5, purpose='ECU into programming session')
        result = result and dut.step(step_6, purpose='Security Access with invalid key')
        result = result and dut.step(step_7, events_and_codes,
                           purpose='ECU to Default session and Read and compare\
                               total_rej_events and event code')
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
