"""

/*********************************************************************************/



Copyright Â© 2022 Volvo Car Corporation. All rights reserved.



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
    Event Code  Event
    0x00        No History reported
    0x01        Invalid securityAccess subfunction SendKey attempt
    0x02        Invalid securityAccess subfunction SendKey attempt and delayTimer is activated
    0x80        Valid securityAccess subfunction SendKey attempt
    Table - Security Access Application Event Code

details: >
    Request security access with invalid key twice to activate security access delay timer. Read
    "Security Access Application" data record with identifier 0xD03C before and after the security
    access with invalid key. And verify 'total rejected event count' is increased by 2 and
    'rejected event code' is '02'.
    steps:
    1. Read security log event DID D03C and extract security event data for rejected events
    2. Extract security event data after security access with invalid key
    3. Security access with invalid key for second time and verify security events data for
       rejected events
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_sec_acc import SecAccessParam
from supportfunctions.support_can import SupportCAN
import supportfunctions.support_service27 as SP27

SC = SupportCAN()
SE27 = SupportService27()
SSA = SecAccessParam()


def security_access_with_invalid_key(dut):
    """
    Security access with invalid key
    Args:
        dut (Dut): An instance of Dut
    Returns:
        Response (str): CAN message receive
    """
    sa_keys = dut.conf.default_rig_config
    result, payload = SE27.activate_security_access_seed_and_calc(dut, sa_keys)
    if not result:
        logging.error("Request seed failed for security access")
        return None

    # Corrupting key payload
    payload[4] = 0xFF
    payload[5] = 0xFF

    # Security access with invalid key
    response = SE27.security_access_send_key(dut, sa_keys, payload)[1]
    SP27.SSA.process_server_response_key(bytearray.fromhex(response))

    # Returning server response
    return SC.can_messages[dut["receive"]][0][2]


def get_rejected_events_and_codes(response):
    """
    Extract security log event data for rejected event from ECU response
    Args:
        response (dict): ECU response
    Returns:
        rejected_events_and_code (dict): Security log for rejected events and codes
    """
    rejected_events_and_code = {'total_successful_events': '',
                                'total_rejected_events': '',
                                'latest_rejected_event_code': ''}

    response_items = response.data['details']['response_items']
    rejected_events_and_code['total_successful_events'] = int(response_items[0]['sub_payload'], 16)
    rejected_events_and_code['total_rejected_events'] = int(response_items[1]['sub_payload'], 16)

    for response_item in response_items:
        if response_item['name'] == "Latest rejected event - Event Code":
            rejected_events_and_code['latest_rejected_event_code'] = response_item['sub_payload']
            break

    return rejected_events_and_code


def extract_security_event_data(dut):
    """
    Read security access application DID 'D03C' and extract events data
    Args:
        dut (Dut): An instance of dut
    Returns:
        rejected_events_and_code (dict): security event data
    """
    response = dut.uds.read_data_by_id_22(bytes.fromhex('D03C'))
    if response.raw[4:6] == '62':
        rejected_events_and_code = get_rejected_events_and_codes(response)
        return rejected_events_and_code

    return None


def verify_response(events_and_code1, events_and_code3):
    """
    Verify security events data
    Args:
        events_and_code1 (dict): Security events data before security access with invalid key
        events_and_code3 (dict): Security events data after security access with invalid key
    Returns:
        (bool): True when total number of rejected events is incremented by 2 and latest
                rejected event code is '02'
    """
    total_rejected_events_latest = events_and_code3['total_rejected_events']
    total_rejected_events = events_and_code1['total_rejected_events']
    latest_rejected_event_code = events_and_code3['latest_rejected_event_code']

    expected_rejected_events = total_rejected_events + 2

    if total_rejected_events_latest == expected_rejected_events :
        if latest_rejected_event_code == '02':
            logging.info("Received security event data for rejected event as expected")
            return True

    logging.error("Test Failed: Expected rejected events counts: %s and rejected event code: '02' "
                  "But received rejected event counts: %s and rejected event count: %s",
                   expected_rejected_events, total_rejected_events_latest,
                   latest_rejected_event_code)
    return False


def step_1(dut: Dut):
    """
    action: Read security log event DID D03C and extract security event data for rejected events
    expected_result: True when successfully extracted security event data
    """
    events_and_code1 = extract_security_event_data(dut)
    if events_and_code1 is not None:
        logging.info("Security event data for rejected events: %s", events_and_code1)
        return True, events_and_code1

    logging.error("Test Failed: Unable to extract security events data for rejected event")
    return False, events_and_code1


def step_2(dut: Dut):
    """
    action: Extract security event data after security access with invalid key
    expected_result: True when successfully extracted security event data after getting
                     NRC-35(invalidKey)
    """
    # Set ECU to extended session
    dut.uds.set_mode(3)

    # Security access with invalid key
    response = security_access_with_invalid_key(dut)
    if response[2:4] != '7F' and response[6:8] != '35':
        logging.error("Test Failed: Expected NRC-35(invalidKey) for security access with "
                      "invalid key, but received %s", response)
        return False

    logging.info("Received negative response with NRC-35(invalidKey) for first time security "
                 "access with invalid key as expected")

    events_and_code2 = extract_security_event_data(dut)
    logging.info("Security event data, after first time security access with invalid key: %s",
                 events_and_code2)

    return True


def step_3(dut: Dut, events_and_code1):
    """
    action: Security access with invalid key for second time and verify security events data
    expected_result: True when total number of rejected events is incremented by 2 and latest
                     rejected event code is '02'
    """
    # Second time security access with invalid key for getting NRC-36(exceededNumberOfAttempts)
    response = security_access_with_invalid_key(dut)
    if response[2:4] != '7F' and response[6:8] != '36':
        logging.error("Test Failed: Expected negative response with "
                      "NRC-36(exceededNumberOfAttempts) for second time security access with "
                      "invalid key, but received %s", response)
        return False, None

    logging.info("Received negative response with NRC-36(exceededNumberOfAttempts) for second "
                    "time security access with invalid key as expected")

    # Set ECU in default session
    dut.uds.set_mode(1)

    events_and_code3 = extract_security_event_data(dut)
    logging.info("Security event data, after second time security access with invalid key: %s",
                 events_and_code3)

    return verify_response(events_and_code1, events_and_code3)


def run():
    """
    Verify security log event for successful event and rejected event
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=60)
        result_step, events_and_code1 = dut.step(step_1, purpose="Read security log event DID D03C"
                                            " and extract security event data for rejected events")
        if result_step:
            result_step = dut.step(step_2, purpose="Extract security event data after security"
                                                   " access with invalid key")
        if result_step:
            result_step = dut.step(step_3, events_and_code1, purpose="Security access with invalid"
                                            " key for second time and verify security events data")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
