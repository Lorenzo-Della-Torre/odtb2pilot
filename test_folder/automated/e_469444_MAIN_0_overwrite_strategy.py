"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 469444
version: 0
title: overwrite strategy

purpose: >
    to reduce the risk of data being erased.

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
    The ECU must record the total number of events reported for
    each event type (TotalNumberOfReportedEvents). For some event types,
    it's important to be able to distinguish between successful- and rejected attempts.
    Hence, the Security Event Header could optionally include a second counter.
    For each event type, one of the two following Security Event Header counter
    structures shall be used; Security Event Header type 1,
    including one single counter of all reported events (TotalNumberOfReportedEvents).
    Security Event Header type 2, including two counters; the first counter keep track of
    the successful attempts (TotalNumberOfSuccessfulEvents) and the second attempt
    counts the number of rejected attempts (TotalNumberOfRejectedEvents).
    This is to be applied when successful and rejected attempts are reported and could be
    separated. Security Event Header type 2 shall be applied when the event type
    contains both successful and rejected events, so for checking that overwrite of events
    TotalNumberOfSuccessfulEvents and TotalNumberOfRejectedEvents are made 16 each as the
    FIFO is Full now one more Event is generated to check it shall not overwritten
    on older event for a second type of event.

"""
import logging
import time
import inspect
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_sec_acc import SecAccessParam
import supportfunctions.support_service27 as SP27

SIO = SupportFileIO()
SE27 = SupportService27()


def get_successful_rejected_events_and_codes(response):
    """
    Read and store total successful events and rejected events and code in dictionary
    Args:
        response(dict): DID response
    Returns:
        events_and_codes(dict): total successful, rejected events and code
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


def security_access_invalid_key(dut: Dut):
    """
    Security access to ECU and corrupt the payload
    Args:
        dut(class object): Dut instance
    Returns:
        Response(str): Can response
    """
    sa_keys: SecAccessParam = {
        "SecAcc_Gen": 'Gen2',
        "fixed_key": '0102030405',
        "auth_key": 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',
        "proof_key": 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), sa_keys)
    SP27.SSA.set_keys(sa_keys)
    result, response = SE27.security_access_request_seed(dut, sa_keys)
    SP27.SSA.process_server_response_seed(bytearray.fromhex(response))
    payload = SP27.SSA.prepare_client_send_key()
    payload[4] = 0xFF
    payload[5] = 0xFF
    result, response = SE27.security_access_send_key(dut, sa_keys, payload)
    result = SP27.SSA.process_server_response_key(bytearray.fromhex(response))
    if result:
        return False
    return True


def step_1(dut: Dut):
    """
    action: Read Security log event DID D046
    expected_result: Positive response with the event data
    """
    dut.uds.set_mode(3)
    response = dut.uds.read_data_by_id_22(b'\xd0\x46')
    # NRC 31 requestOutOfRange
    if response.raw[6:8] != '31':
        events_and_codes = get_successful_rejected_events_and_codes(response)
        if response.raw[4:6] == '62':
            return True, events_and_codes
    logging.error("Test Failed: NRC 31 requestOutOfRange received")
    return False, None


def step_2(dut: Dut):
    """
    action: Security Access to ECU for 15 times
    expected_result: Positive response
    """
    result = []
    sa_keys: SecAccessParam = {
        "SecAcc_Gen": 'Gen2',
        "fixed_key": '0102030405',
        "auth_key": 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',
        "proof_key": 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), sa_keys)
    dut.uds.set_mode()
    for _ in range(15):
        dut.uds.set_mode(2)
        result.append(SE27.activate_security_access_fixedkey(
            dut, sa_keys, step_no=272, purpose='Security Access'))
        time.sleep(2)
    if all(result):
        return True
    logging.error(
        "Test error: Security Access to ECU not successful for 15 times")
    return False


def step_3(dut: Dut, events_and_codes):
    """
    action: Read Security log event DID D046
    expected_result: Total number of successful events is
                     incremented by 15 Latest successful event
                     code is '80'
    """
    dut.uds.set_mode()
    dut.uds.set_mode(3)
    time.sleep(2)
    response = dut.uds.read_data_by_id_22(b'\xd0\x46')
    latest_events_and_codes = get_successful_rejected_events_and_codes(
        response)
    if latest_events_and_codes['total_successful_events'] \
        == events_and_codes['total_successful_events'] + 15 \
            and latest_events_and_codes['latest_successful_event_code'] == '80':
        return True
    logging.error(
        "Test Failed: Successful event count is not increased or event code is wrong")
    return False


def step_4(dut: Dut):
    """
    action: Security Access to ECU with invalid key for 16 times
    expected_result: Positive response for Request Seed
                     Negative response for Send Key
    """
    result = []
    for count in range(16):
        dut.uds.set_mode(2)
        result.append(security_access_invalid_key(dut))
        if count % 2 != 0:
            time.sleep(10)
    if all(result):
        return True
    logging.error("Test error: Security Access to ECU with invalid key\
        is not successful for 16 times")
    return False


def step_5(dut: Dut, events_and_codes):
    """
    action: Read Security log event DID D046
    expected_result: Total number of Rejected events is incremented by 16
                     Latest rejected event code is '02'
    """
    dut.uds.set_mode()
    dut.uds.set_mode(3)
    time.sleep(2)
    response = dut.uds.read_data_by_id_22(b'\xd0\x46')
    latest_events_and_codes = get_successful_rejected_events_and_codes(
        response)
    if latest_events_and_codes['total_rejected_events'] \
        == events_and_codes['total_rejected_events'] + 16 \
            and latest_events_and_codes['latest_rejected_event_code'] == '02':
        return True, latest_events_and_codes
    logging.error(
        "Test Failed: Rejected event count is not increased or event code is wrong")
    return False, None


def step_6(dut: Dut):
    """
    action: Entering to Programming session and Security Access to ECU
    expected_result: Positive response
    """
    dut.uds.set_mode(2)
    sa_keys: SecAccessParam = {
        "SecAcc_Gen": 'Gen2',
        "fixed_key": '0102030405',
        "auth_key": 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',
        "proof_key": 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), sa_keys)
    result = SE27.activate_security_access_fixedkey(
        dut, sa_keys, step_no=6, purpose='Security Access')
    if result:
        return True
    logging.error("Test error: Security Access to ECU is not successful")
    return False


def step_7(dut: Dut, events_and_codes):
    """
    action: Read Security log event DID D046
            Checking the overwrite is successful in right position of the latest
            successful events by comparing previous successful events and latest
            successful events and rejected events is not incremented.
    expected_result: Positive response
    """
    dut.uds.set_mode()
    dut.uds.set_mode(3)
    time.sleep(2)
    response = dut.uds.read_data_by_id_22(b'\xd0\x46')
    latest_events_and_codes = get_successful_rejected_events_and_codes(
        response)
    if latest_events_and_codes['total_rejected_events'] \
        == events_and_codes['total_rejected_events'] \
        and latest_events_and_codes['total_successful_events'] \
            == events_and_codes['total_successful_events'] + 1:
        return True
    logging.error("Test error: Security Access is not successful or \
        successful event not incremented")
    return False


def step_8(dut: Dut):
    """
    action: Read Security log event DID D046
    expected_result: Positive response and event data
    """
    dut.uds.set_mode()
    dut.uds.set_mode(3)
    time.sleep(2)
    response = dut.uds.read_data_by_id_22(b'\xd0\x46')
    events_and_codes = get_successful_rejected_events_and_codes(response)
    if response.raw[4:6] == '62':
        return True, events_and_codes
    logging.error("Test Failed: Response 62 not received")
    return False, None


def step_9(dut: Dut):
    """
    action: Security Access to ECU with invalid key
    expected_result: Positive response for Request Seed
                     Negative response for Send Key
    """
    dut.uds.set_mode(2)
    result = security_access_invalid_key(dut)
    if result:
        return True
    logging.error("Test Failed: Security access with invalid not successful")
    return False


def step_10(dut: Dut, events_and_codes):
    """
    action: Read Security log event DID D046
            Checking the overwrite is successful in right position of the latest
            rejected events by comparing rejected events and code.
            Overwrite Strategy Steps:
            1. Checked FIFO is full in previous steps by security access to ECU for
                16 times each negative and positive response.
            2. Identify right position to overwrite latest rejected events which
                is (length of list / 2) + 1
            3. Compare the previous rejected event code is '02' with delayTimer activated
                and the latest rejected event code is '01' without delayTimer
                and total rejected events is incremented by 1 to make sure the
                overwrite is successful and FIFO write event on first position and it
                works as per the requirement.
    expected_result: Positive response
    """
    dut.uds.set_mode()
    dut.uds.set_mode(3)
    time.sleep(2)
    response = dut.uds.read_data_by_id_22(b'\xd0\x46')
    latest_rej_event_code_index = int(
        len(response.data['details']['response_items'])/2 + 1)
    latest_events_and_codes = get_successful_rejected_events_and_codes(
        response)
    event_code_latest = \
        response.data['details']['response_items'][latest_rej_event_code_index]['sub_payload']
    if latest_events_and_codes['total_rejected_events'] \
        == events_and_codes['total_rejected_events'] + 1 \
        and latest_events_and_codes['total_successful_events'] \
        == events_and_codes['total_successful_events'] and \
        event_code_latest == '01' and \
            events_and_codes['latest_rejected_event_code'] == '02':
        return True
    logging.error("Test Failed: Overwrite is not successful or \
        rejected event count is not incremented or event code is wrong")
    return False


def run():
    """ Supporting functional requests """
    dut = Dut()
    start_time = dut.start()
    result = False
    try:
        dut.precondition(400)
        result, events_and_codes = dut.step(step_1, purpose='Read DID D046')
        if result:
            result = dut.step(
                step_2, purpose='Security Access with 15 valid key')
        if result:
            result = dut.step(step_3, events_and_codes,
                              purpose='ECU to Default session and compare with latest '
                              'and previous successful events and event code')
        if result:
            result = dut.step(
                step_4, purpose='Security Access with 16 invalid key')

        if result:
            result, events_and_codes = dut.step(step_5, events_and_codes,
                                                purpose='ECU to Default session and compare '
                                                'with latest and previous successful '
                                                        'events and event code')
        if result:
            result = dut.step(step_6,
                              purpose='Set to Programming mode '
                              'and Security Access with valid key')
        if result:
            result = dut.step(step_7, events_and_codes, purpose='total_succ_events_latest '
                              'dose not overwrites with total_succ_events')
        if result:
            result, events_and_codes = dut.step(
                step_8, purpose='Read DID D046')
        if result:
            result = dut.step(
                step_9, purpose='Security Access to ECU with invalid key')
        if result:
            result = dut.step(step_10, events_and_codes,
                              purpose='total_rejected_events_latest dose not overwrites '
                              'with total_rejected_events')
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
