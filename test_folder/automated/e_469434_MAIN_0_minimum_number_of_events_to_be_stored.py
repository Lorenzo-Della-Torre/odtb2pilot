"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 469434
version: 0
title: Security Event Header, Minimum number of events to be stored.
purpose:
    To be able to analyse the history.

description:
    The ECU must be able to store at least 20 events (for each type defined),
    but 100 events are recommended.
    If both successful- and rejected attempts are reported,
    half of the event records for successful- and rejected attempts respectively must be stored.
    Otherwise, the history of e.g. the rejected attempts could be lost
    (the log is filled with only successful attempts).
    The first half (e.g. 10 when 20 events in total are stored) are reserved for successful attempts
    and the last part is for the rejected attempts.

    Example 1.
    Pre-condition; 19 event records are stored out of total 20 (9 successful, 10 rejected),
    Event record 1; Successful attempt, e.g. a file is verified OK.
    Event record 2; Successful attempt
    Event record 3; Successful attempt
    Event record 4; Successful attempt
    Event record 5; Successful attempt
    Event record 6; Successful attempt
    Event record 7; Successful attempt
    Event record 8; Successful attempt
    Event record 9; Successful attempt
    Event record 10; No history
    Event record 11; Rejected attempt, e.g. the file verification failed.
    Event record 12; Rejected attempt
    Event record 13; Rejected attempt
    Event record 14; Rejected attempt
    Event record 15; Rejected attempt
    Event record 16; Rejected attempt
    Event record 17; Rejected attempt
    Event record 18; Rejected attempt
    Event record 19; Rejected attempt
    Event record 20; Rejected attempt
    If the next reported event is a rejected attempt,
    a record for a successful attempt must not be overwritten but a record
    (oldest) for a rejected attempt shall be overwritten according to the overwrite strategy.
    Note.
    The number of events that is stored must be balanced with respect to the available memory.

details:
    Verify logs for all event types contain at least 20 events. Read all related dids and verify
    that they have at least 20 events of one kind or at least 10 successful and 10 rejected events
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO

SIO = SupportFileIO()


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
            response_item_dict["time_list"].append(resp_item["name"])
        elif valid_response_items["event_code"] in resp_item["name"]:
            response_item_dict["event_code_list"].append(resp_item["name"])
        elif valid_response_items["additional_data"] in resp_item["name"]:
            response_item_dict["additional_data_list"].append(resp_item["name"])

    return response_item_dict


def find_events(did_response, parameters, did):
    """
    Find events in the response
    Args:
        did_response (str): ECU response
        parameters (dict): Valid response items
        did (str): DID
    Returns:
        found_events (list): Events
    """
    resp_items = did_response.details["response_items"]

    if 'Total number of reported Events'.lower() in resp_items[0]['name'].lower():
        found_events = extract_response_items(did_response, parameters['valid_response_items'])

    elif ('Total number of successful events'.lower() in resp_items[0]['name'].lower())\
        and ('Total number of rejected events'.lower() in resp_items[1]['name'].lower()):
        found_events = {"successful_events" : [],
                        "rejected_events" : []}

        found_events_1 = extract_response_items(did_response,
                            parameters['valid_successful_response_items'])
        found_events["successful_events"].append(found_events_1)


        found_events_2 = extract_response_items(did_response,
                                  parameters['valid_rejected_response_items'])
        found_events["rejected_events"].append(found_events_2)

    else:
        logging.error("Expected 'Total number of reported Events' or"
                      " 'Total number of successful events' for did %s, received %s", did,
                       did_response.details["response_items"][0]['name'])
        logging.error("Expected 'Total number of rejected events' for did %s, received %s", did,
                       did_response.details["response_items"][1]['name'])
        return []

    return found_events


def evaluate_did_event(dut, did, parameters):
    """
    Verify ReadDataByIdentifier(0x22) service with respective DID and test if DID is included in the
    reply from the ECU. Also find and validate events
    Args:
        dut (Dut): An instance of Dut
        did (str): DID
        parameters(dict): Valid response items
    Returns:
        events (dict): Successful events, rejected events and events
    """
    did_response = dut.uds.read_data_by_id_22(bytes.fromhex(did))
    if did_response.raw[4:6] == '62':
        events = find_events(did_response, parameters, did)
        return events
    logging.error("Expected positive response '62', received %s for did %s", did_response.raw, did)
    return None


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


def verify_latest_successful_rejected_event(events):
    """
    Verify DIDs have at least 10 successful and 10 rejected events
    Args:
        events (dict): Successful events and rejected events
    Returns:
        (bool): True when successfully verified successful events and rejected events
    """
    time_list_length_successful = len(events['successful_events'][0]['time_list'])
    time_list_length_rejected = len(events['rejected_events'][0]['time_list'])
    time_list_length = time_list_length_successful>=10 and time_list_length_rejected>=10

    event_code_list_length_successful =\
    len(events['successful_events'][0]['event_code_list'])
    event_code_list_length_rejected =\
    len(events['rejected_events'][0]['event_code_list'])
    event_code_list_length = event_code_list_length_successful>=10 and\
        event_code_list_length_rejected>=10

    additional_data_list_length_successful =\
    len(events['successful_events'][0]['additional_data_list'])
    additional_data_list_length_rejected =\
    len(events['rejected_events'][0]['additional_data_list'])
    additional_data_list_length = additional_data_list_length_successful>=10 and\
        additional_data_list_length_rejected>=10

    if time_list_length and event_code_list_length and additional_data_list_length:
        return True
    return False


def verify_latest_event(events):
    """
    verify DIDs have at least 20 events of one kind
    Args:
        events (dict): Events
    Returns:
        (bool): True when successfully verified events
    """
    time_list_length = len(events['time_list'])
    event_code_list_length = len(events['event_code_list'])
    additional_data_list_length = len(events['additional_data_list'])
    if time_list_length>=20 and event_code_list_length>=20 and\
        additional_data_list_length>=20:
        return True
    return False


def step_1(dut : Dut, parameters):
    """
    action: Read all event type DIDs and verify DIDs have at least 20 events of one kind or at
            least 10 successful and 10 rejected events
    expected_result: True when events of DIDs are successfully verified
    """
    unique_dids = find_unique_did(dut)
    results = []

    for did in unique_dids:
        events = evaluate_did_event(dut, did, parameters)
        if events is None:
            logging.error("Expected positive response '62' for did %s", did)
            results.append(False)
        else:
            if len(events) == 2:
                result = verify_latest_successful_rejected_event(events)
                results.append(result)
            elif len(events) == 3:
                result = verify_latest_event(events)
                results.append(result)
            else:
                logging.error("Invalid structure of did %s", did)
                results.append(False)

    if all(results) and len(results) != 0:
        logging.info("Correct events of all the DIDs is received as expected")
        return True

    logging.error("Test Failed: Invalid events of one or more DIDs")
    return False


def run():
    """
    Verify logs for all event types contain at least 20 events. Read all related dids and verify
    that they have at least 20 events of one kind or at least 10 successful and 10 rejected events
    """
    dut = Dut()

    start_time = dut.start()
    result = False

    parameters_dict = {'valid_response_items': {},
                       'valid_successful_response_items': {},
                       'valid_rejected_response_items': {}}
    try:
        dut.precondition(timeout=90)
        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result = dut.step(step_1, parameters, purpose='Read all event type DIDs and verify'
                          ' DIDs have at least 20 events of one kind or at least 10 successful'
                          ' and 10 rejected events')

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
