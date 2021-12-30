"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 469437
version: 1
title: Security Access Application
purpose: >
    Define general event types that are applicable for many ECUs.

description: >
    The ECU shall implement event type "Security Access Application"
    data record with identifier 0xD03C. The event type is for diagnostic
    service SecurityAccess when the ECU application is running,
    i.e. is not in ProgrammingSession.

    Event Header: SecurityEventHeaderType 2 shall be applied, i.e. using two counters.
    Size 32+32 bits. Event Records Time. Size 32 bits EventCode. As defined in
    "Table - Security Access Application Event Code". Size 8 bits.
    AdditionalEventData: Byte value of subfunction requestSeed ("security access level").
    Size 8 bits.
    Event Code	Event
    0x00	    No History reported
    0x01	    Invalid securityAccess subfunction SendKey attempt
    0x02	    Invalid securityAccess subfunction SendKey attempt and delayTimer is activated
    0x80	    Valid securityAccess subfunction SendKey attempt
    Table - Security Access Application Event Code

details: >
    Read Security log event DID D03C and save the rejected counter value
    Create an Event, Security Access Application Event code 0x02,
    Invalid securityAccess subfunction SendKey attempt and delayTimer is activated
    Read Security log event DID D03C and verify counter has incremented and
    Latest event code is 0x02
"""

import logging
import inspect
import time
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_sec_acc import SecAccessParam
from supportfunctions.support_can import SupportCAN
import supportfunctions.support_service27 as SP27

SC = SupportCAN()
SE27 = SupportService27()
SIO = SupportFileIO()


def security_access_negative_response(dut: Dut):
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
    SP27.SSA.process_server_response_seed(
        bytearray.fromhex(response))
    payload = SP27.SSA.prepare_client_send_key()
    payload[4] = 0xFF
    payload[5] = 0xFF
    result2, response = SE27.security_access_send_key(
        dut, sa_keys, payload)
    result = result and result2
    result = SP27.SSA.process_server_response_key(
        bytearray.fromhex(response))
    # Server response
    return SC.can_messages['HvbmToHvbmdpUdsDiagResponseFrame'][0][2]


def get_rejected_events_and_code(response):
    """
    Read and store total rejected events and rejected events code in dictionary
    Args:
        response(dict): DID response
    Returns:
        rejected_events_and_code(dict): total rejected events and code
    """
    rejected_events_and_code = {'total_rejected_event': '',
                                'latest_rejected_event_code': ''}
    for response_item in response.data['details']['response_items']:
        if response_item['name'] == "Total number of rejected events":
            rejected_events_and_code['total_rejected_event'] = int(
                response_item['sub_payload'], 16)
        if response_item['name'] == "Latest rejected event - Event Code":
            rejected_events_and_code['latest_rejected_event_code'] = \
                response_item['sub_payload']
        if rejected_events_and_code['total_rejected_event'] != '' and \
                rejected_events_and_code['latest_rejected_event_code'] != '':
            break
    return rejected_events_and_code


def step_1(dut: Dut):
    """
    action: Read Security log event DID D03C
    expected_result: Positive response with the event data
    """
    response = dut.uds.read_data_by_id_22(b'\xd0\x3C')
    # NRC 31 requestOutOfRange
    if response.raw[6:8] != '31':
        rejected_events_and_code = get_rejected_events_and_code(response)
        return True, rejected_events_and_code
    logging.error("Test Failed: NRC 31 requestOutOfRange received")
    return False, None


def step_2(dut: Dut):
    """
    action: Security Access to ECU with invalid key
    expected_result: Negative response to send key with NRC 36
    """
    for _ in range(2):
        dut.uds.set_mode(2)
        response = security_access_negative_response(dut)
        if response is None:
            logging.error("Test Failed: Empty response")
        elif response[2:4] == '7F' and response[6:8] == '36':
            return True
    return False


def step_3(dut: Dut, rejected_events_and_code):
    """
    action: Read Security log event DID D03C
    expected_result: Total number of Rejected events is incremented
                     Latest rejected event code is '02'
    """
    dut.uds.set_mode()
    time.sleep(2)
    response = dut.uds.read_data_by_id_22(b'\xd0\x3C')
    rejected_events_and_code_latest = get_rejected_events_and_code(response)
    if rejected_events_and_code_latest['total_rejected_event'] == \
        rejected_events_and_code['total_rejected_event'] + 2 \
            and rejected_events_and_code['latest_rejected_event_code'] == '02':
        return True
    logging.error(
        "Test Failed: Rejected event count is not increased Or the event code is wrong")
    return False


def run():
    """ Supporting functional requests """
    dut = Dut()
    start_time = dut.start()
    result = False
    try:
        dut.precondition()
        result, rejected_events_and_code = dut.step(
            step_1, purpose='Read Security log event DID D03C')
        if result:
            result = dut.step(
                step_2, purpose='Security Access with Invalid key')
        if result:
            result = dut.step(step_3, rejected_events_and_code,
                                purpose='Read Security log event DID D03C with event code 02')

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
