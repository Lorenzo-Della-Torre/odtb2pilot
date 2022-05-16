"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



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
    Define general event types that are applicable for many ECUs.

description: >
    The ECU shall implement event type "Security Access ProgrammingSession"
    data record with identifier 0xD046.
    The event type is for diagnostic service SecurityAccess
    when the ECU is running in ProgrammingSession.
    The structure as defined in "REQPROD 469437
    Event Type - Security Access Application" shall be applied,
    but the Time per event record shall be removed from the structure as many ECUs
    have no knowledge of the time (or internal counter that is always
    incrementing and never resets) in this state
    Event Header SecurityEventHeaderType 2. Size 32+32 bits.
    Event Records
    EventCode; See "Table - Security Access Application Event Code" defined in "REQPROD 469437
    Event Type – Security Access Application". Size 8 bits.
    AdditionalEventData Byte value of subfunction requestSeed ("security access level").
    Size 8 bits.


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
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_sec_acc import SupportSecurityAccess

SC = SupportCAN()
SE10 = SupportService10()
SE27 = SupportService27()
SIO = SupportFileIO()
SSA = SupportSecurityAccess()

def security_access_negative_response(dut: Dut, sa_keys):
    """
    Security access to ECU and corrupt the payload
    Args:
        dut(class object): Dut instance
    Returns:
        Response(str): Can response
    """

    result, sa_calculated = SE27.activate_security_access_seed_and_calc(dut,
                                                                        sa_keys)

    #modify key to send to get negative reply
    pl_modified = SSA.sa_key_calculated_distort(sa_calculated)
    #pl_modified = sa_calculated

    result = result and\
             SE27.activate_security_access_send_calculated(dut,
                                                           sa_keys,
                                                           pl_modified)

    if not result:
        # Server response
        return SC.can_messages['HvbmToHvbmdpUdsDiagResponseFrame'][0][2]
    return None


def get_saps_events_and_code(response):
    """
    Read and store total successful events and rejected events code in dictionary
    Args:
        response(dict): DID response
    Returns:
        get_saps_events_and_code(dict): total rejected events and code
    """
    sa_events_and_code = {'total_successful_events': '',
                          'latest_successful_event_code': '',
                          'total_rejected_events': '',
                          'latest_rejected_event_code': ''}
    for response_item in response.data['details']['response_items']:
        if response_item['name'] == "Total number of successful events":
            sa_events_and_code['total_successful_events'] = int(
                response_item['sub_payload'], 16)
        if response_item['name'] == "Total number of rejected events":
            sa_events_and_code['total_rejected_events'] = int(
                response_item['sub_payload'], 16)

        if response_item['name'] == "Latest successful event - Event Code":
            sa_events_and_code['latest_successful_event_code'] = \
                response_item['sub_payload']
        if response_item['name'] == "Latest rejected event - Event Code":
            sa_events_and_code['latest_rejected_event_code'] = \
                response_item['sub_payload']

        if sa_events_and_code['total_rejected_events'] != '' and \
                sa_events_and_code['latest_rejected_event_code'] != '':
            break
    return sa_events_and_code


def step_1(dut: Dut):
    """
    action: Read Security log event DID D046
    expected_result: Positive response with the event data
    """
    response = dut.uds.read_data_by_id_22(b'\xd0\x46')
    # NRC 31 requestOutOfRange
    logging.info("Step1, response.raw %s ", response.raw)
    logging.info("Step1, response.raw [6:8] %s ", response.raw[6:8])
    logging.info("Step1, type response.raw  %s ", type(response.raw))
    # response.raw is of type str.
    # we get a positive reply (no NRC) on HVBM
    # if testing on ecu where D046 is not implemented you might get
    # '31' : 'requestOutOfRange'
    if response.raw[6:8] != '31':
        events_and_code = get_saps_events_and_code(response)
        return True, events_and_code, response
    logging.error("Test Failed: NRC 31 requestOutOfRange received")
    return False, None, response


def step_2(dut: Dut, sa_keys):
    """
    action: Security Access to ECU with valid key
    expected_result: positive response - SA granted
    """
    result = SE10.diagnostic_session_control_mode2(dut, stepno=2)
    logging.info("Step_2: Requesting SA with valid key.")

    result2, sa_calculated = SE27.activate_security_access_seed_and_calc(dut,
                                                                         sa_keys)
    result = result and result2 and\
             SE27.activate_security_access_send_calculated(dut,
                                                           sa_keys,
                                                           sa_calculated)
    return result


def step_3(dut: Dut,
           events_and_code,
           response1):
    """
    action:
    Set to default session.
    Read Security log event DID D046.
    Get latest Total number of rejected events
    Check the rejected event counter is increased by 2
    expected_result: Total number of Rejected events is incremented
                     Latest rejected event code is '02'
    """
    result = SE10.diagnostic_session_control_mode1(dut, stepno=3)
    time.sleep(2)

    response = dut.uds.read_data_by_id_22(b'\xd0\x46')
    if response.raw[6:8] == '31':
        return False, response
    events_and_code1 = get_saps_events_and_code(response)

    logging.info("Events and codes: %s", )
    logging.info("before SA attempt    %s", response1.raw)
    logging.info("after valid attempt  %s", response.raw)

    if not (events_and_code1['total_successful_events'] == \
            events_and_code['total_successful_events'] + 1 \
            and events_and_code1['latest_successful_event_code'] == '80'):
        logging.error(
            "Test Failed: Rejected event count is not increased Or the event code is wrong")
        return False, response
    return result, response

def step_4(dut: Dut, sa_keys):
    """
    action: Security Access to ECU with invalid key
    expected_result: Negative response to send key with NRC 36
    """
    result = SE10.diagnostic_session_control_mode2(dut, stepno=4)
    for _ in range(2):
        logging.info("Step_4: Requesting SA with distorted key.")
        response = security_access_negative_response(dut, sa_keys)
        if response is None:
            result = False
            logging.error("Test Failed: Empty response")
        elif response[2:4] == '7F' and response[6:8] == '36':
            logging.info("Correct reply to distorted key.")
        time.sleep(6) #have to wait at least 5sec before next seed request
    logging.info("Step_4 result %s", result)
    return result


def step_5(dut: Dut,
           events_and_code,
           response1,
           response2):
    """
    action:
    Set to default session.
    Read Security log event DID D046.
    Get latest Total number of rejected events
    Check the rejected event counter is increased by 2
    expected_result: Total number of Rejected events is incremented
                     Latest rejected event code is '02'
    """
    dut.uds.set_mode()
    time.sleep(2)
    response = dut.uds.read_data_by_id_22(b'\xd0\x46')
    logging.info("Step5, response to d046 request: %s", response)
    events_and_code_latest = get_saps_events_and_code(response)
    logging.info("Step_5, events_and_code latest %s", events_and_code_latest)
    logging.info("First info attempts before attempts")
    logging.info("Events and codes: %s", events_and_code)

    logging.info("Latestt info after 2 rejected events")
    logging.info("Events and codes: %s", )
    logging.info("All responses to 22 D046: ")
    logging.info("before SA attempt    %s", response1.raw)
    logging.info("after valid attempt  %s", response2.raw)
    logging.info("after 2 invalid ones %s", response.raw)

    if events_and_code_latest['total_rejected_events'] == \
        events_and_code['total_rejected_events'] + 2 \
            and events_and_code_latest['latest_rejected_event_code'] == '02':
        return True
    logging.error(
        "Test Failed: Rejected event count is not increased Or the event code is wrong")
    logging.error("Test failed. Rejected events before: %s",
                  events_and_code['total_rejected_events'])
    logging.error("Test failed. Rejected events now   : %s",
                  events_and_code_latest['total_rejected_events'])
    logging.error("Test failed. Latest rejected event code (expect: '02'): %s",
                  events_and_code_latest['latest_rejected_event_code'])
    return False


def run():
    """ Supporting functional requests """
    dut = Dut()
    start_time = dut.start()
    result = False

    platform=dut.conf.rigs[dut.conf.default_rig]['platform']
    sa_keys = {
        "SecAcc_Gen" : dut.conf.platforms[platform]['SecAcc_Gen'],
        "fixed_key": dut.conf.platforms[platform]["fixed_key"],
        "auth_key": dut.conf.platforms[platform]["auth_key"],
        "proof_key": dut.conf.platforms[platform]["proof_key"]
    }

    try:
        dut.precondition(timeout=120)

        #Read our DID D046 before doing SA request
        result, events_and_code, response1 = dut.step(
            step_1, purpose ='Read Security log event DID D046')

        #make a successful attempt to get SA access
        result = result and dut.step(step_2,
                                     sa_keys,
                                     purpose='Read Sec log event DID D046 with sucessful attempt')

        #check if reply to D046 reflects successful atempt
        if result:
            result, response2 = dut.step(
                step_3,
                events_and_code,
                response1,
                purpose='Read Security log event DID D046')
        logging.info("After step3. result %s", result)

        if result:
            result = dut.step(
                step_4, sa_keys, purpose='Triggering Event Code 0x02')
        if result:
            result = dut.step(step_5,
                              events_and_code,
                              response1,
                              response2,
                              purpose='Read Security log event DID D046 with event code 02')

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
