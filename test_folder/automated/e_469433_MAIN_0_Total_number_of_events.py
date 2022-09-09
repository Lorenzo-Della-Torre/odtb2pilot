"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



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

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_service27 import SupportService27
import supportfunctions.support_service27 as SP27

SSA = SupportSecurityAccess()
SE27 = SupportService27()


def get_successful_rejected_events_and_codes(response):
    """
    Extract event data from ECU response
    Args:
        response (dict): ECU response
    Returns:
        events_and_codes (dict): Total successful, rejected events and codes
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
        (bool): True when security access is not successful for invalid key
    """
    sa_keys=dut.conf.default_rig_config
    result, payload = SE27.activate_security_access_seed_and_calc(dut, sa_keys)
    if not result:
        logging.error("Test Failed: Request seed unsuccessful")
        return False

    # Corrupt payload
    payload[4] = 0xFF
    payload[5] = 0xFF

    result, response = SE27.security_access_send_key(dut, sa_keys, payload)

    result = result and (SP27.SSA.process_server_response_key(bytearray.fromhex(response)) == 0)

    if not result:
        logging.info("Security access denied as expected")
        return True

    logging.error("Test Failed: Unexpected security access")
    return False


def step_1(dut: Dut):
    """
    action: Read DID D046 and extract security log event data
    expected_result: True when received positive response '62' with event data
    """
    response = dut.uds.read_data_by_id_22(bytes.fromhex('D046'))

    if response.raw[4:6] == '62':
        events_and_codes = get_successful_rejected_events_and_codes(response)
        return True, events_and_codes

    logging.error("Test Failed: Expected positive response '62', received %s", response.raw)
    return False, None


def step_2(dut: Dut):
    """
    action: Set ECU to programming session and security access
    expected_result: True when security access is successfully in programing session
    """
    # Sleep time to avoid NRC37
    time.sleep(5)
    # Set ECU in programming session
    dut.uds.set_mode(2)

    result = SE27.activate_security_access_fixedkey(dut, dut.conf.default_rig_config)
    if not result:
        logging.error("Test Failed: Unable to unlock ECU")

    return result


def step_3(dut: Dut, events_and_codes):
    """
    action: Read DID D046 in default session and verify event data for successful event
    expected_result: True when total number of successful events is incremented by 1 and latest
                     successful event code is '80'
    """
    # Set ECU in default session
    dut.uds.set_mode(1)

    response = dut.uds.read_data_by_id_22(bytes.fromhex('D046'))
    latest_events_and_codes = get_successful_rejected_events_and_codes(response)

    if events_and_codes['total_successful_events'] + 1 == \
          latest_events_and_codes['total_successful_events'] :
        latest_successful_event_code = latest_events_and_codes['latest_successful_event_code']
        if latest_successful_event_code == '80':
            logging.info("Successfully verified security log event data for successful event")
            return True

        logging.error("Test Failed: Successful event not increased or received unexpected event "
                      "code '%s' instead of expected '80'", latest_successful_event_code)
    return False


def step_4(dut: Dut):
    """
    action: Set ECU to programming session and security access to ECU for rejected event
    expected_result: True when security access is not successful with invalid key
    """
    # Set ECU in programming session
    dut.uds.set_mode(2)

    return security_access_with_invalid_key(dut)


def step_5(dut: Dut, events_and_codes):
    """
    action: Read DID D046 in default session and verify event data for rejected event
    expected_result: True when total number of rejected events is incremented by 1 and latest
                     rejected event code is '01'
    """
    # Set ECU in default session
    dut.uds.set_mode(1)

    response = dut.uds.read_data_by_id_22(bytes.fromhex('D046'))
    latest_events_and_codes = get_successful_rejected_events_and_codes(response)

    if events_and_codes['total_rejected_events'] + 1 == \
        latest_events_and_codes['total_rejected_events'] :
        latest_rejected_event_code = latest_events_and_codes['latest_rejected_event_code']
        if latest_rejected_event_code == "01":
            logging.info("Successfully verified security log event data for rejected event")
            return True

    logging.error("Test Failed: Rejected event not increased or received unexpected event code '%s'"
                  "instead of expected '01'", latest_rejected_event_code)
    return False


def step_6(dut: Dut):
    """
    action: ECU reset and verify active diagnostic session
    expected_result: True when ECU is in default session
    """
    # ECU reset
    dut.uds.ecu_reset_1101()

    # Wait 2 seconds
    time.sleep(2)

    # Verify active diagnostic session
    response = dut.uds.active_diag_session_f186()
    if response.data["details"]["mode"] == 1:
        logging.info("ECU is in default session as expected")
        return True

    logging.error("Test Failed: Expected ECU to be in default session, received mode %s",
                   response.data["details"]["mode"])
    return False


def run():
    """
    Read security log event DID D046 and verify event data from response for successful event and
    rejected event.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=60)
        result_step, events_and_codes = dut.step(step_1, purpose="Read DID D046 and extract event "
                                                                 "data")
        if result_step:
            result_step = dut.step(step_2, purpose="Set ECU to programming session and security "
                                                   "access")
        if result_step:
            result_step = dut.step(step_3, events_and_codes, purpose="Read DID D046 in default "
                                          "session and verify event data for successful event")
        if result_step:
            result_step = dut.step(step_4, purpose = "Set ECU to programming session and security "
                                                     "access with invalid key")
        if result_step:
            result_step = dut.step(step_5, events_and_codes, purpose="Read DID D046 in default "
                                              "session and verify event data for rejected event")
        if result_step:
            result_step = dut.step(step_6, purpose="ECU reset and verify active diagnostic "
                                                   "session")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
