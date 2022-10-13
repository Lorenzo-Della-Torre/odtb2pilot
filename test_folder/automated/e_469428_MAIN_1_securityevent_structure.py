"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 469428
version: 1
title: SecurityEvent structure
purpose: >
	Define a common structure for security events.

description: >
    Every security event shall use the SecurityEvent structure, including
    • Time: The time when the event was detected.
    • Source: The entity in the ECU that is reporting the event, e.g. a verification component
      used for Signature Verification of a file. Source is (optional) and shall be omitted by
      default (see note).
    • EventCode: Code (number) used to describe the Event, e.g. 1 = SignatureVerification failed,
      Invalid Signature Data. Each event type uses its own set of EventCodes. EventCode=0 shall
      be used to indicate 'No History', i.e. no record reported. Values 0x01-0x7F shall be applied
      for "failed/rejected" attempts and 0x80-0xFE for successful respectively.
    • AdditionalEventData: Additional data, e.g. a file name, Certificate details, IP Addresses,
      etc. This information is related to e.g. event type and its EventCode.
    • The value 0xFF shall be applied as default value for event entries that are empty, e.g. Time
      and AdditionalEventData when required information is not available.
    The supplier must provide a list of the defined EventCodes.
    Note.
    When defining the actual diagnostic identifier (DID) according to the SecurityEvent structure,
    the Source might be obsolete if there is only one component reporting the specific event type.

details: >
    Verify structure of all EventType DIDs
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO

SIO = SupportFileIO()


def extract_event_position(event_name):
    """
    Extracts all digits from the event_name string
    Args:
        event_name (str): Event name
    Returns:
        event_num (int): Event number
    """
    event_num_str = '0'
    event_num = 0
    for count in range(2):
        if event_name[count].isdigit():
            event_num_str += event_name[count]
    event_num = int(event_num_str, 10)
    return event_num


def extract_response_items(did_response, valid_response_items):
    """
    Extract response_items that contains any of the values belong to the keys "time",
    "event_code", additional_data" in valid_response_items
    Args:
        did_response (str): DID response from ECU
        valid_response_items (dict): Time, eventcode and additional data
    Returns:
        response_item_dict (dict): Valid response items
    """
    response_item_dict = {"time_list" : [],
                          "event_code_list" : [],
                          "additional_data_list" : []}

    for resp_item in did_response.details["response_items"]:
        if valid_response_items["time"] in resp_item["name"]:
            response_item_dict["time_list"].append(resp_item)
        elif valid_response_items["event_code"] in resp_item["name"]:
            response_item_dict["event_code_list"].append(resp_item)
        elif valid_response_items["additional_data"] in resp_item["name"]:
            response_item_dict["additional_data_list"].append(resp_item)

    return response_item_dict


def get_sub_payload_value(response_items, number_of_events):
    """
    Get sub payload value for each event from response items dict
    Args:
        response_items (dict): Response items
        number_of_events (int): Number of expected events
    Returns:
        event_list (list): Events and sub_payload
    """
    event_list = []
    for _ in range(number_of_events):
        event_list.append({})

    for resp_item_type in response_items:
        for resp_item in response_items[resp_item_type]:
            event_pos = extract_event_position(resp_item["name"])
            if event_pos > 0:
                event_list[event_pos-1][resp_item["name"]] = resp_item["sub_payload"]
            else:
                event_list[event_pos][resp_item["name"]] = resp_item["sub_payload"]
    return event_list


def find_events(did_response, parameters):
    """
    Find events in the response
    Args:
        did_response (str): ECU response
        parameters (dict): Valid response items
    Returns:
        found_events (list): Events
    """
    name_of_last_event = did_response.details["response_items"][-2]['name']
    number_of_events = extract_event_position(name_of_last_event)

    response_items = extract_response_items(did_response, parameters['valid_response_items'])
    found_events = get_sub_payload_value(response_items, number_of_events)

    return found_events


def get_substring(event, sub_string):
    """
    Find missing elements from the event and log them
    Args:
        event (dict): Event
        sub_string (str): Sub string to find
    Returns:
        element (list): Missing event type
    """
    element = list(filter(lambda x: sub_string in x, list(event.keys()) ))
    return element


def log_missing_events(events, did):
    """
    Find missing elements from the event and log them
    Args:
        events (list): Events
        did (str): DID
    Returns:
        (bool): True when successfully verified the event structure
    """
    search_list = ['Time', 'Event Code', 'Additional Event Data']
    logging.info("~~~~~~ Checking structure for DID %s in the sddb ~~~~~~", did)
    result = True
    for event in events:
        event_key = list(event.keys())[0].split(" - ")[0]
        for sub_string in search_list:
            element = get_substring(event, sub_string)
            if len(element) == 0:
                logging.error("%s - %s is missing", event_key, sub_string)
                result = False

    return result


def validate_events(events, did):
    """
    Check all events contain the same number of response_items
    Verify if successful events have codes in the range 0x80-0xFE and rejected events have codes
    in the range 0x01-0x7F
    Args:
        events (list): Dictionaries containing events
        did (str): DID
    Returns:
        (bool): True when event codes are successfully verified
    """
    result = log_missing_events(events, did)

    for event in events:
        for entry in event.keys():
            if "Latest successful event - Event Code".lower() in entry.lower():
                event_code = event[entry]
                if 'FE' < event_code < '80':
                    logging.error("Event code for '%s' should be > 0x7F but is %s", entry,
                                   event[entry])
                    return False

            if "Latest rejected event - Event Code".lower() in entry.lower():
                event_code = event[entry]
                if '7F' < event_code < '01':
                    logging.error("Event code for '%s' should be < 0x80 but is %s", entry,
                                   event[entry])
                    return False

    return True and result


def evaluate_did_structure(dut, did, parameters):
    """
    Verify ReadDataByIdentifier(0x22) service with respective DID and test if DID is included in the
    reply from the ECU. Also find and validate events
    Args:
        dut (Dut): An instance of Dut
        did (str): DID
        parameters(dict): Valid response items
    Returns:
        (bool): True when events are successfully validate
    """
    result = True
    did_response = dut.uds.read_data_by_id_22(bytes.fromhex(did))

    if did_response.raw[4:6] != '62':
        logging.error("Test Failed: Expected positive response for DID %s, received %s", did,
                       did_response.raw)
        return False

    events = find_events(did_response, parameters)

    for i, event in enumerate(events):
        if not event:
            logging.error("No response_items found for event number %s", str(i+1))
            result = False

    if result:
        result = validate_events(events, did)

    return result


def find_event_type_did(sddb_dids):
    """
    Find EventType DIDs from sddb
    Args:
        sddb_dids (list): Sddb DIDs
    Returns:
        sddb_did_list (list): EventType sddb dids
    """
    sddb_did_list = []
    for did_sddb, did_data in sddb_dids.items():
        if did_data['name'].find('Event Type') != -1 or did_data['name'].find('EventType') != -1:
            sddb_did_list.append(did_sddb)
    return sddb_did_list


def get_sddb_dids(dut):
    """
    Get EventType DIDs from sddb
    Args:
        dut (Dut): An instance of Dut
    Returns:
        sddb_did_list (list): EventType sddb DIDs
    """
    sddb_did_list = []
    sddb_dids = dut.conf.rig.sddb_dids["app_did_dict"]
    sddb_did_list = find_event_type_did(sddb_dids)

    sddb_dids = dut.conf.rig.sddb_dids["pbl_did_dict"]
    sddb_did_list.extend(find_event_type_did(sddb_dids))

    sddb_dids = dut.conf.rig.sddb_dids["sbl_did_dict"]
    sddb_did_list.extend(find_event_type_did(sddb_dids))

    return sddb_did_list


def find_unique_did(dut):
    """
    Prepare unique EventType DIDs from sddb
    Args:
        dut (Dut): An instance of Dut
    Returns:
        unique_sddb_dids (list): Unique EventType sddb DIDs
    """
    sddb_dids = get_sddb_dids(dut)
    unique_sddb_dids = []

    for did in sddb_dids:
        if did not in unique_sddb_dids:
            unique_sddb_dids.append(did)
    return unique_sddb_dids


def step_1(dut : Dut, parameters):
    """
    action: Verify EventType DIDs structure
    expected_result: True when structure of DIDs are successfully verified
    """
    unique_dids = find_unique_did(dut)
    results = []

    for did in unique_dids:
        result = evaluate_did_structure(dut, did, parameters)
        if result:
            results.append(True)
        else:
            results.append(False)

    if all(results) and len(results) != 0:
        logging.info("Correct structure of all the DIDs is received as expected")
        return True

    logging.error("Test Failed: Invalid structure of one or more DIDs")
    return False


def run():
    """
    Verify structure of all EventType DIDs
    """
    dut = Dut()

    start_time = dut.start()
    result = False

    parameters_dict = {'valid_response_items': {}}
    try:
        dut.precondition(timeout=60)
        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result = dut.step(step_1, parameters, purpose='Verify EventType DIDs structure')

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
