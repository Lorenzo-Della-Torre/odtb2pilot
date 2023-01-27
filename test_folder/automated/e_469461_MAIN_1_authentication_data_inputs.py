"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 469461
version: 1
title: Authentication data Inputs
purpose: >
    Define the input data to be part of the actual Authentication Data calculation.

description: >
    The Authentication Data shall be calculated using all stored SecurityEvents and
    the SecurityEventHeader (Authentication Data itself excluded) as input data.
    A single Authentication Data is calculated per event type The Authentication Data
    shall always be appended next to the last event record for an event type, big endian.

details: >
    Verify authentication data is generated per event type.
    Steps-
        1. Read security log DID and get authentication data
        2. Increment successful event
        3. Read security log again and verify authentication data is generated for latest event
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_service27 import SupportService27

SE27 = SupportService27()


def get_event_count_auth_data(response):
    """
    Get total number of successful event count and authentication data from security log
    Args:
        response(dict): Security log response
    Returns:
        event_auth_data(dict): Successful event and authentication data
    """
    event_auth_data = {'successful_event': 0,
                       'auth_data': ''}
    for response_item in response.data['details']['response_items']:
        if response_item['name'] == "Total number of successful events":
            event_auth_data['successful_event'] = int(response_item['sub_payload'], 16)
        if response_item['name'] == "Authentication Data":
            event_auth_data['auth_data'] = response_item['sub_payload']

    if event_auth_data['auth_data'] != '':
        return event_auth_data

    return None


def step_1(dut: Dut):
    """
    action: Read Security log event DID D046
    expected_result: True with the event data
    """
    response = dut.uds.read_data_by_id_22(bytes.fromhex('D046'))
    if response.raw[4:6] != '62':
        logging.error("Test Failed: Invalid DID response %s", response.raw[4:6])
        return False, None

    event_auth_data = get_event_count_auth_data(response)
    if event_auth_data is None:
        logging.error("Test Failed: Event or authentication data is empty")
        return False, None

    return True, event_auth_data


def step_2(dut: Dut):
    """
    action: Set ECU to programming session and Security Access to ECU
    expected_result: True when security access successful
    """
    dut.uds.set_mode(2)

    # Sleep time to avoid NRC37
    time.sleep(5)

    result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config)
    if result:
        logging.info("Security access successful")
        return True
    logging.error("Test Failed: Security access not successful")
    return False


def step_3(dut: Dut, event_auth_data):
    """
    action: Set ECU to default session and read security log event DID D046
    expected_result: True when authentication data are unique per event type
                     and Total number of successful events is incremented by 1
    """
    dut.uds.set_mode(1)

    response = dut.uds.read_data_by_id_22(bytes.fromhex('D046'))
    latest_event_auth_data = get_event_count_auth_data(response)

    # Compare authentication data is generated per event type
    auth_result = latest_event_auth_data['auth_data'] != event_auth_data['auth_data']

    # Verify total successful event is increased by 1
    event_result = latest_event_auth_data['successful_event'] == \
            event_auth_data['successful_event'] + 1

    if auth_result and event_result:
        logging.info("Authentication data is unique per event type")
        return True

    logging.error("Test Failed: Expected unique authentication data per event type "
                  "received latest: %s equal to previous: %s",
                  latest_event_auth_data['auth_data'], event_auth_data['auth_data'])
    return False


def run():
    """ Verify authentication data is generated per event type """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=30)

        result_step, event_auth_data = dut.step(step_1, purpose='Read DID D046')

        if result_step:
            result_step = dut.step(step_2, purpose='Security Access to ECU')

        if result_step:
            result_step = dut.step(step_3, event_auth_data, purpose='Verify authentication '
                                   'data is calculated per event type')

        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
