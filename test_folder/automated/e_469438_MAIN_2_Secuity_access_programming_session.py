"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 469438
version: 2
title: Security Access Programming session
purpose: >
    Define general event types that are applicable for many ECUs. If there are other requirements
    that limits the possibility to log data, e.g. if the ECU is in a state where it lacks
    capabilities to write to non-volatile memory, the security audit log shall not override those
    requirements. Such an example might be bootloaders that lack write/erase non-volatile memory
    instructions.

description: >
    The ECU shall implement event type "Security Access ProgrammingSession" data record with
    identifier 0xD046. The event type is for diagnostic service SecurityAccess when the ECU is
    running in ProgrammingSession.

    The structure as defined in "REQPROD 469437 : Event Type - Security Access Application" shall
    be applied, but the Time per event record shall be removed from the structure as many ECUs have
    no knowledge of the time (or internal counter that is always incrementing and never resets) in
    this state:

    Event Header: SecurityEventHeaderType 2. Size 32+32 bits.
    Event Records:
    EventCode: See "Table - Security Access Application Event Code" defined in "REQPROD 469437 :
    Event Type - Security Access Application". Size 8 bits.
    AdditionalEventData: Byte value of subfunction requestSeed ("security access level"). Size 8
    bits.

    Access Control: Option (3) as defined in "REQPROD 469450 : Security Audit Log - Access Control"
    shall be applied.

details: >
    Read Security log event DID D046 and save the rejected counter value
    Create an Event Security Access Programming session Event code 0x02,
    Invalid securityAccess subfunction SendKey attempt
    Set to default mode and delayTimer is activated
    Read Security log event DID D046 and verify counter has incremented and
    Latest event code is 0x02
"""

import logging
import time
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_sec_acc import SupportSecurityAccess

SC = SupportCAN()
SE27 = SupportService27()
SSA = SupportSecurityAccess()

def security_access_negative_response(dut):
    """
    Security access to ECU with corrupted payload
    Args:
        dut (Dut): An instance of Dut
    Returns:
        Response (str): Can response
    """
    sa_keys=dut.conf.default_rig_config
    result, sa_calculated = SE27.activate_security_access_seed_and_calc(dut, sa_keys)
    # Modify key to send to get negative reply
    pl_modified = SSA.sa_key_calculated_distort(sa_calculated)

    result = result and SE27.activate_security_access_send_calculated(dut, sa_keys, pl_modified)

    if not result:
        return SC.can_messages[dut['receive']][0][2]
    return None


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


def step_1(dut: Dut):
    """
    action: Read DID D046 and extract security log event data
    expected_result: ECU should give positive response '62' and event data should be extracted
    """
    response = dut.uds.read_data_by_id_22(bytes.fromhex('D046'))

    if response.raw[4:6] == '62':
        events_and_codes = get_successful_rejected_events_and_codes(response)
        logging.info("Successfully extracted event data after received positive response for DID "
                     "D046")
        return True, events_and_codes

    logging.error("Test Failed: Expected positive response '62', received %s", response.raw)
    return False, None


def step_2(dut: Dut):
    """
    action: Set ECU to programming session and security access
    expected_result: Security access should be successful in programing session
    """
    # Set ECU in programming session
    dut.uds.set_mode(2)

    # Sleep time to avoid NRC37
    time.sleep(5)

    result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config)
    if result:
        logging.info("Security access successful in programming session")
        return True

    logging.error("Test Failed: Unable to unlock ECU in programming session")
    return False


def step_3(dut: Dut, events_and_codes):
    """
    action: Read DID D046 in default session and verify event data for successful event
    expected_result: Total number of successful events should be incremented by 1 and latest
                     successful event code should be '80'
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
    action: Security Access to ECU with invalid key
    expected_result: Negative response with NRC-36(exceededNumberOfAttempts)
    """
    # Set ECU in programming session
    dut.uds.set_mode(2)

    # Sleep time to avoid NRC37
    time.sleep(5)

    # Security access with invalid key
    response = security_access_negative_response(dut)
    if response[2:4] != '7F' and response[6:8] != '35':
        logging.error("Test Failed: Expected NRC-35(invalidKey) for security access with "
                      "invalid key, but received %s", response.raw)
        return False

    # Second time security access with invalid key for getting NRC-36(exceededNumberOfAttempts)
    response = security_access_negative_response(dut)
    if response[2:4] == '7F' and response[6:8] == '36':
        logging.info("Received negative response with NRC-36(exceededNumberOfAttempts) for second "
                     "time security access with invalid key as expected")
        return True

    logging.error("Test Failed: Expected negative response with NRC-36(exceededNumberOfAttempts) "
                  "for second time security access with invalid key, but received %s",response.raw)
    return False


def step_5(dut: Dut, events_and_codes):
    """
    action: Read DID D046 in default session and verify event data for rejected event
    expected_result: Total number of rejected events should be incremented by 2 and latest
                     rejected event code should be '02'
    """
    # Set ECU in default session
    dut.uds.set_mode(1)

    response = dut.uds.read_data_by_id_22(bytes.fromhex('D046'))
    latest_events_and_codes = get_successful_rejected_events_and_codes(response)
    latest_rejected_event_code = latest_events_and_codes['latest_rejected_event_code']

    if events_and_codes['total_rejected_events'] + 2 == \
        latest_events_and_codes['total_rejected_events'] :

        if latest_rejected_event_code == "02":
            logging.info("Successfully verified security log event data for rejected event")
            return True

    logging.error("Test Failed: Rejected event not increased or received unexpected event code "
                  "'%s' instead of '02'", latest_rejected_event_code)
    return False


def step_6(dut: Dut):
    """
    action: Set ECU to programming session and security access
    expected_result: Security access should be successful in programing session
    """
    # Set ECU in programming session
    dut.uds.set_mode(2)

    # Sleep time to avoid NRC37 after two failed security access
    time.sleep(10)

    result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config)
    if result:
        logging.info("Security access successful in programming session")
        return True

    logging.error("Test Failed: Unable to unlock ECU in programming session")
    return False


def run():
    """
    Read Security log event DID D046 and also verify events an codes for successful and rejected
    event
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=90)

        result_step, events_and_code = dut.step(step_1, purpose ="Read DID D046 and extract "
                                                                 "security log event data")
        if result_step:
            result_step = dut.step(step_2, purpose="Set ECU to programming session and security "
                                                   "access")
        if result_step:
            result_step = dut.step(step_3,events_and_code,purpose="Read DID D046 in default "
                                   "session and verify event data for successful event")
        if result_step:
            result_step = dut.step(step_4, purpose="Security Access to ECU with invalid key")
        if result_step:
            result_step = dut.step(step_5, events_and_code, purpose="Read DID D046 in default "
                                   "session and verify event data for rejected event")
        if result_step:
            result_step = dut.step(step_6, purpose="Set ECU to programming session and security "
                                                   "access")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
