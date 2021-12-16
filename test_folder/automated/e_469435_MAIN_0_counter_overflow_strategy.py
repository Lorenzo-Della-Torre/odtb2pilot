"""
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
    Read with one of the Security log event DID D046 and
    Store the response Total number of successful events and RejectedEvents
    Create an Event; Security Access ProgrammingSession with
    Valid securityAccess subfunction SendKey attempt
    Create an Event; Security Access ProgrammingSession with
    Invalid securityAccess subfunction SendKey attempt
    Send ECU back to Default session to check DID D046
    Check the Event has been logged in D046 DID and Event Code is 0x80 and 0x01
    Compare with previously saved response Total number of successful and Rejected events
    Total number of successful and Rejected events will be incremented by 1
    Do the ECU Reset 11 01
    Send ECU back to Default session to check DID D046
    Compare with previously saved response Total number of successful and Rejected events
    Counters should be same as before the ECU Reset
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

SE27 = SupportService27()
SIO = SupportFileIO()


def get_total_events(response):
    """
    expected result: return dict of total successful and rejected events
    """
    total_events = {'total_successful_event': 0,
                    'total_rejected_event': 0}
    for response_item in response.data['details']['response_items']:
        if response_item['name'] == "Total number of successful events":
            total_events['total_successful_event'] = int(
                response_item['sub_payload'], 16)
        if response_item['name'] == "Total number of rejected events":
            total_events['total_rejected_event'] = int(
                response_item['sub_payload'], 16)
        if total_events['total_successful_event'] != 0 and \
                total_events['total_rejected_event'] != 0:
            break
    return total_events


def get_latest_events_code(response):
    """
    expected result: return dict of latest successful and rejected events code
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
    action: Read Security log event DID D046
    expected_result: Positive response with the event data
    """
    response = dut.uds.read_data_by_id_22(b'\xd0\x46')
    total_events = get_total_events(response)
    if response.raw[4:6] == '62':
        return True, total_events
    return False, None


def step_2(dut: Dut):
    """
    action: Set ECU to Programming Session
    expected_result: Positive response
    """
    dut.uds.set_mode(2)
    res = dut.uds.active_diag_session_f186()
    result = bool(res.data['sid'] == '62' and res.data['details']['mode'] == 2)
    return result


def step_3(dut: Dut):
    """
    action: Security Access to ECU
    expected_result:Positive response
    """
    sa_keys: SecAccessParam = {
        "SecAcc_Gen": 'Gen2',
        "fixed_key": '0102030405',
        "auth_key": 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',
        "proof_key": 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), sa_keys)
    result = SE27.activate_security_access_fixedkey(
        dut, sa_keys, step_no=3, purpose='Security Access with Valid key')
    return result


def step_4(dut: Dut, total_events):
    """
    action: Set ECU to Default session and
            Read Security log event DID D046
    expected_result: Total number of successful incremented by 1
                     Latest successful event code is '80'
    """
    dut.uds.set_mode()
    time.sleep(2)
    response = dut.uds.read_data_by_id_22(b'\xd0\x46')
    total_events_latest = get_total_events(response)
    events_code_latest = get_latest_events_code(response)
    if total_events_latest['total_successful_event'] == \
            total_events['total_successful_event'] + 1 and \
            events_code_latest['latest_successful_event_code'] \
            == '80':
        return True
    return False


def step_5(dut: Dut):
    """
    action: Security Access to ECU with invalid key
    expected_result: Negative response
    """
    dut.uds.set_mode(2)
    sa_keys: SecAccessParam = {
        "SecAcc_Gen": 'Gen2',
        "fixed_key": '0102030405',
        "auth_key": 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',
        "proof_key": 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), sa_keys)
    SP27.SSA.set_keys(sa_keys)
    result, response = SE27.security_access_request_seed(dut, sa_keys)
    SP27.SSA.process_server_response_seed(
        bytearray.fromhex(response))
    payload = SP27.SSA.prepare_client_send_key()
    payload[4] = 0xFF
    payload[5] = 0xFF
    result, response = SE27.security_access_send_key(dut, sa_keys, payload)
    result = SP27.SSA.process_server_response_key(
        bytearray.fromhex(response))
    if result:
        return False
    return True


def step_6(dut: Dut):
    """
    action: ECU Reset
    expected_result: Positive Response
    """
    response = dut.uds.ecu_reset_1101()
    result = bool(response.data['sid'] == '51')
    return result


def step_7(dut: Dut, total_events):
    """
    action: Set ECU to Default session and
            Read Security log event DID D046
    expected_result:
                    DID D046 Event Counters are same as before ECU Reset
                    Total number of successful and rejected events is incremented by 1
                    Latest successful event code is '80' and Rejected event code is '01'
    """
    dut.uds.set_mode()
    time.sleep(3)
    response = dut.uds.read_data_by_id_22(b'\xd0\x46')
    total_events_latest = get_total_events(response)
    events_code_latest = get_latest_events_code(response)
    if total_events_latest['total_successful_event'] == \
            total_events['total_successful_event'] + 1 and \
            events_code_latest['latest_successful_event_code'] \
            == '80' and \
            total_events_latest['total_rejected_event'] == \
            total_events['total_rejected_event'] + 1 and \
            events_code_latest['latest_rejected_event_code'] == '01':
        return True
    return False


def run():
    """ Supporting functional requests """
    dut = Dut()
    start_time = dut.start()
    result = False
    try:
        dut.precondition()
        result, total_events = dut.step(step_1, purpose='Read DID D046')
        if result:
            result = dut.step(step_2, purpose='ECU into programming session')
        if result:
            result = dut.step(step_3, purpose='Security Access with Valid Key')
        if result:
            result = dut.step(step_4, total_events,
                          purpose='Successful and Rejected Counter and \
                               codes verification before ECU reset')
        if result:
            result = dut.step(step_5, purpose='Security Access with Invalid key')
        if result:
            result = dut.step(step_6, purpose='ECU Reset')
        if result:
            result = dut.step(step_7, total_events,
                          purpose='Successful and Rejected Counter and \
                               codes verification After ECU reset')
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
