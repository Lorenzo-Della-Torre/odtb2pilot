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
    Event Code	Event
    0x00	    No History reported
    0x01	    Invalid securityAccess subfunction SendKey attempt
    0x02	    Invalid securityAccess subfunction SendKey attempt and delayTimer is activated
    0x80	    Valid securityAccess subfunction SendKey attempt
    Table - Security Access Application Event Code

details: >
    Read security log event DID D03C and save the rejected counter value create an event, security
    access application event code 0x02, invalid securityAccess subfunction SendKey attempt and
    delayTimer is activated read security log event DID D03C and verify counter has incremented and
    latest event code is 0x02
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
    result, response = SE27.security_access_send_key(dut, sa_keys, payload)
    result = result and SP27.SSA.process_server_response_key(bytearray.fromhex(response))

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
    rejected_events_and_code = {'total_rejected_events': '',
                                'latest_rejected_event_code': ''}

    response_items = response.data['details']['response_items']
    rejected_events_and_code['total_rejected_events'] = int(response_items[1]['sub_payload'], 16)

    for response_item in response_items:
        if response_item['name'] == "Latest rejected event - Event Code":
            rejected_events_and_code['latest_rejected_event_code'] = response_item['sub_payload']
            break

    return rejected_events_and_code


def step_1(dut: Dut):
    """
    action: Read security log event DID D03C
    expected_result: True when successfully extracted event data
    """
    response = dut.uds.read_data_by_id_22(bytes.fromhex('D03C'))
    if response.raw[4:6] == '62':
        rejected_events_and_code = get_rejected_events_and_codes(response)
        return True, rejected_events_and_code

    logging.error("Test Failed: Expected positive response '62', but received %s", response.raw)
    return False, None


def step_2(dut: Dut):
    """
    action: Security access with invalid key
    expected_result: True when received negative response with NRC 36 for send key
    """
    for _ in range(2):
        dut.uds.set_mode(2)
        response = security_access_with_invalid_key(dut)

        if response is None:
            logging.error("Test Failed: Received empty response for security access")
            return False

        if response[2:4] == '7F' and response[6:8] == '36':
            logging.info("Received negative response with NRC-36 for security access as expected")
            return True

    logging.error("Test Failed: Expected negative response with NRC 36, received %s", response.raw)
    return False


def step_3(dut: Dut, rejected_events_and_code):
    """
    action: Read Security log event DID D03C
    expected_result: True when total number of rejected events is incremented by 2 and latest
                     rejected event code is '02'
    """
    # Set ECU in default session
    dut.uds.set_mode(1)

    response = dut.uds.read_data_by_id_22(bytes.fromhex('D03C'))
    rejected_events_and_code_latest = get_rejected_events_and_codes(response)

    total_rejected_events_latest = rejected_events_and_code_latest['total_rejected_events']
    total_rejected_events = rejected_events_and_code['total_rejected_events']
    latest_rejected_event_code = rejected_events_and_code['latest_rejected_event_code']

    if total_rejected_events_latest == total_rejected_events + 2 :
        if latest_rejected_event_code == '02':
            logging.info("Received security event data for rejected event as expected")
            return True

    logging.error("Test Failed: Rejected event count is not increased or the event code is wrong")
    return False


def run():
    """
    Verify security log event for successful event and rejected event
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=30)
        result_step, rejected_events_and_code = dut.step(step_1, purpose="Read Security log event"
                                                                         " DID D03C")
        if result_step:
            result_step = dut.step(step_2, purpose="Security access with invalid key")
        if result_step:
            result_step = dut.step(step_3, rejected_events_and_code, purpose="Verify response of"
                                                                             " read DID D03C")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
