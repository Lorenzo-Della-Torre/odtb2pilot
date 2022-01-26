"""
reqprod: 469428
version: 0
title: SecurityEvent structure
purpose: >
    Define a common structure for security events.

description: >
    Every security event shall use the SecurityEvent structure, including
    • Time: The time when the event was detected.
    • Source: The entity in the ECU that is reporting the event, e.g. a verification component
    used for Signature Verification of a file. Source is (optional) and shall be omitted by default
    (see note).
    • EventCode: Code (number) used to describe the Event, e.g. 1 = SignatureVerification failed,
    Invalid Signature Data. Each event type uses its own set of EventCodes. EventCode=0 shall be
    used to indicate 'No History', i.e. no record reported. Values 0x01-0x7F shall be applied for
    "failed/rejected" attempts and 0x80-0xFE for successful respectively.
    • AdditionalEventData: Additional data, e.g. a file name, Certificate details, IP Addresses,
    etc. This information is related to e.g. event type and its EventCode.

    • The value 0xFF shall be applied as default value for event entries that are empty, e.g. Time
    and AdditionalEventData when required information is not available.

    The supplier must provide a list of the defined EventCodes.

    Note.
    When defining the actual diagnostic identifier (DID) according to the SecurityEvent structure,
    the Source might be obsolete if there is only one component reporting the specific event type.



details:
    This script verifies the structure of certain DIDs. This is done by verifying the sddb
    file and making sure it contains all the events it should. The sddb file is also used to
    extract the information about all the events from the ECU response.

    Lastly both the number of events and structure for each event is examined.

    Script needs to be updated to fully cover requirement.
    Event data: only verified that successful > 0x7F and rejected < 0x80.
    Validation needs to be made on event with header type 1.

"""
import logging

from hilding.dut import Dut
from hilding.dut import DutTestError

from supportfunctions.support_service27_2 import SupportService27
import supportfunctions.pretty_print as pp
import supportfunctions.pretty_print_GUI as ppGUI

SS27 = SupportService27()

def __extract_number(input_str):
    """Extracts all digits from a string

    Args:
        str (str): arbitrary string

    Returns:
        string: string containing only the digits found in str
    """
    ret = ""
    for char in input_str:
        if char.isdigit():
            ret += char
    return ret


def __extract_response_items(res, valid_response_items):
    """Transforms a udsResponse into a dictionary containing all response_items that contains
    any of the values belong to the keys "time", "event_code", additional_data"
    in valid_response_items

    Args:
        res (udsResponse): A udsResponse, probably from read_data_by_id_22()
        valid_response_items (dict): A dictionary containing the desired strings for
        time, event code and additional data.

    Returns:
        dict: A dictionary containing all valid response items found in
        res.
    """
    ret = {
        "times" : [],
        "event_codes" : [],
        "additional_datas" : []}

    for resp_item in res.details["response_items"]:
        if valid_response_items["time"] in resp_item["name"]:
            ret["times"].append(resp_item)
        if valid_response_items["event_code"] in resp_item["name"]:
            ret["event_codes"].append(resp_item)
        if valid_response_items["additional_data"] in resp_item["name"]:
            ret["additional_datas"].append(resp_item)

    return ret

def __build_event_list(response_items, nbr_of_events):
    """Transforms a dictionary containing response items
    (best extracted using __extract_response_items()) into
    a list with events.

    Args:
        response_items (dict): Dictionary containing response items that should be put
        together to create complete events.
        nbr_of_events (float/int/str): Needed to know how many events we expect to find

    Returns:
        list: A list containing all events found
    """
    ret_event_list = []
    for _ in range(int(nbr_of_events)):
        ret_event_list.append({})

    for resp_item_type in response_items:
        for resp_item in response_items[resp_item_type]:
            number_found_in_resp_item = False
            for i in range(int(nbr_of_events)):
                if str(i+2) == __extract_number(resp_item["name"]):
                    ret_event_list[i+1][resp_item["name"]] = resp_item["sub_payload"]
                    number_found_in_resp_item = True
                    break
            if not number_found_in_resp_item:
                ret_event_list[0][resp_item["name"]] = resp_item["sub_payload"]

    return ret_event_list



def __find_events(res):
    """Takes a response i.e. from read_data_by_id_22 and returns a list
    of events found in the response.

    Args:
        res (UdsResponse): Message received from ECU

    Returns:
        list: A list with dictionaries containing all the events found in the response
    """
    nbr_events = int(res.details["response_items"][-2]['name'][0:2])

    header_type = 0
    resp_items = res.details["response_items"]
    if 'Total number of reported Events' in resp_items[0]['name']:
        header_type = 1
    elif 'Total number of successful events' in resp_items[0]['name']:
        if 'Total number of rejected events' in resp_items[1]['name']:
            header_type = 2
            nbr_events = nbr_events * 2
    else:
        logging.error("Neither header type 1 or type 2 found \n %s \n %s",
            res.details["response_items"][0]['name'],
            res.details["response_items"][1]['name'])
        return []

    found_events = []

    if header_type == 1:
        valid_response_items = {
            "time" : "Latest event - Time",
            "event_code" : "Latest event - Event Code",
            "additional_data" : "Latest event - Additional Event Data"}

        response_items = __extract_response_items(res, valid_response_items)
        found_events = __build_event_list(response_items, nbr_events)

    if header_type == 2:
        valid_response_items = {
            "time" : "Latest successful event - Time",
            "event_code" : "Latest successful event - Event Code",
            "additional_data" : "Latest successful event - Additional Event Data"}

        response_items = __extract_response_items(res, valid_response_items)
        found_events = __build_event_list(response_items, nbr_events/2)

        valid_response_items = {
            "time" : "Latest rejected event - Time",
            "event_code" : "Latest rejected event - Event Code",
            "additional_data" : "Latest rejected event - Additional Event Data"}

        response_items = __extract_response_items(res, valid_response_items)
        found_events += __build_event_list(response_items, nbr_events/2)

    return found_events

def __validate_number_of_response_items(events, did):
    ok_to_exclude_time = True

    events_sorted = []#contains the events sorted i.e events_sorted[0] contains event(s) with 1 attr
    for _ in range(3):
        events_sorted.append([])

    for event in events:
        events_sorted[len(event)-1].append(event)

    different_sizes_found = False
    events_found = False
    for sorted_events in events_sorted:
        if sorted_events:
            if events_found:
                different_sizes_found = True
                break
            events_found = True

    if different_sizes_found:
        for i,sorted_events in enumerate(events_sorted):
            if sorted_events:
                if i < 2 and not ok_to_exclude_time:
                    logging.error("Time is missing in the structure for DID %s", did)
                    return False
                logging.error("The following event(s) has faulty structure for did %s:", did)
                for event in sorted_events:
                    event_name_only = list(event.keys())[0].split("-")[0]
                    logging.error(event_name_only)
                return False

    return True

def __validate_events(events, did):
    """Check if all event contain the same number of response_items.
    Test if successful events have codes >= 0x80 according to reqs.
    Tests if rejected events have codes > 0x80

    Args:
        events (list): list with dictionaries containing events
        did (str): did id

    Returns:
        boolean: Result from the controls
    """

    result = __validate_number_of_response_items(events, did)

    for event in events:
        if "Latest successful event - Event Code" in event:
            if int(event["Latest successful event - Event Code"], 16) < 120:
                logging.error("Event code should be > 0x7F but is %s",
                event["Latest successful event - Event Code"])
                return False
        if "Latest rejected event - Event Code" in event:
            if int(event["Latest rejected event - Event Code"], 16) > 119:
                logging.error("Event code should be < 0x80 but is %s",
                event["Latest rejected event - Event Code"])
                return False

    return True and result

def __evaluate_did(dut: Dut, did: str):
    result = True
    res = dut.uds.read_data_by_id_22(bytes.fromhex(did))

    logging.debug("ECUs response for %s : %s", did, res)

    try:
        if res.empty() or res.data["did"] != did:
            logging.error("The response from the ECU is empty")
            return False
    except KeyError:
        logging.error("The response from the ECU does not contain the DID id (%s)", did)
        return False

    events = __find_events(res)

    for i,event in enumerate(events):
        logging.debug(event)
        if not event:
            logging.error("No response_items found for event number %s", str(i))
            result = False

    result = __validate_events(events, did) and result

    return result

def step_1(dut : Dut):
    """
    action:
        Test DID D046

    expected_result:
        DID has the correct structure
    """
    result = __evaluate_did(dut, "D046")

    logging.info("Step: %s: Result teststep: %s",
    dut.uds.step,
    result)

    return result

def step_2(dut: Dut):
    """
    action:
        Test DID D048

    expected_result:
        DID has the correct structure
    """
    result = __evaluate_did(dut, "D048")

    logging.info("Step: %s: Result teststep: %s",
    dut.uds.step,
    result)

    return result

def step_3(dut: Dut):
    """
    action:
        Test DID D0B7

    expected_result:
        DID has the correct structure
    """
    result = __evaluate_did(dut, "D0B7")

    logging.info("Step: %s: Result teststep: %s",
    dut.uds.step,
    result)

    return result

def step_4(dut: Dut):
    """
    action:
        Test DID D0C1

    expected_result:
        DID has the correct structure
    """
    result = __evaluate_did(dut, "D0C1")

    logging.info("Step: %s: Result teststep: %s",
    dut.uds.step,
    result)

    return result

def step_5(dut: Dut):
    """
    action:
        Test DID D03C

    expected_result:
        DID has the correct structure
    """
    result = __evaluate_did(dut, "D03C")

    logging.info("Step: %s: Result teststep: %s",
    dut.uds.step,
    result)

    return result

def step_6(dut: Dut):
    """
    action:
        Test DID D0B8

    expected_result:
        DID has the correct structure
    """
    result = __evaluate_did(dut, "D0B8")

    logging.info("Step: %s: Result teststep: %s",
    dut.uds.step,
    result)

    return result

def step_7(dut: Dut):
    """
    action:
        Test DID D0BC

    expected_result:
        DID has the correct structure
    """
    result = __evaluate_did(dut, "D0BC")

    logging.info("Step: %s: Result teststep: %s",
    dut.uds.step,
    result)

    return result

def run():
    """
    Run - Call other functions from here

    """
    #DON'T FORGET TO REMOVE ALL PRINTS IN SCRIPT WHEN THIS IS FIXED!!!
    logging.warning("Script needs to be updated to fully cover requirement.\
Event data: only verified that successful > 0x7F and rejected < 0x80.\
Validation needs to be made on event with header type 1")

    dut = Dut()

    start_time = dut.start()
    result = False
    try:
        # dut.precondition(timeout=3600)
        ppGUI.test(dut)
        pp.subscribe_to_did(dut, "FD40", duration=5)

        #Extended mode
        dut.uds.set_mode(3)

        print(dut.uds.read_data_by_id_22(bytes.fromhex('FD40')))

        sid = b'\x27'

        """
        1 byte
        01	For accessing services in programmingSession: requestDownload, …
        03	For read services used at OEM workshops and production
        05	For write services and executing routine controls used at OEM workshops and production

        15	Reserved for diagnostic firewall
        17	Reserved for diagnostic firewall
        41/42	For accessing diagnostic services requiring secure diagnostic communication using 0x84.
        Always unique keys.
        """
        access_type = b'\x01'


        """
        2 bytes
        clientRequestSeed: 	0x01
        serverResponseSeed:	0x02
        clientSendKey: 	0x03
        """
        message_id = b'\x00\x01'

        """
        2 bytes
        0x0000	Reserved. Do not use.
        0x0001	AES-128-CMAC (message authentication code generation)
        AES-128-CTR (for encryption of plaintext data)
        0x0002-0xFFFE	Spare, for future growth.
        0xFFFF	Reserved. Do not use.
        """
        authentication_message = b'\x00\x01'

        """
        16 bytes
        """
        iv = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

        res = dut.uds.generic_ecu_call(sid + access_type + message_id + authentication_message + iv)
        print(res)

        #res = dut.uds.generic_ecu_call(b'\x27\x05' + b'' + b'')
        # res = dut.uds.generic_ecu_call(b'\x27\x01' + b'' + b'')
        # print(res)
        # res = dut.uds.generic_ecu_call(b'\x27\x05' + b'\x00' + b'\x0001' + b'\x01' + b'\x55' + b'\x55')
        # print(res)

        # print(SS27.security_access_request_seed(dut, {"SecAcc_Gen" : 'Gen2'}))

    except DutTestError as error:
        logging.error("Test failed: %s", error)
        result = False
    finally:
        dut.postcondition(start_time, result)

if __name__ == '__main__':
    run()