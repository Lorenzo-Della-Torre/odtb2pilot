"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 486677
version: 0
title: Event logging rate limitation
purpose:
    Rate limiting for events is required to prevent event log flooding.

description: >
    ECU shall implement rate limitation for events reported per each event
    type in order to prevent flooded events to event logger. An event is dropped
    and not logged if number of events per each event type reported to event logger
    within a configurable time interval passes a configurable threshold.
    Dropped events count shall not be included in "number of reported events"
    counter(s) in Security Event Header of reported eventtype. Instead,
    such flooded events for each event type shall be logged to "Event Type – Event Logging
    Service" with event code "0x06 (Events reported too frequently to logger)" and
    additional data as "Event type identifier + number of dropped events count",
    defined as per "REQPROD 486617; Event Type - Event Logging Service".
    Note; Configuration thresholds should be designed by ECU suppliers and are not
    specified in this document.
    Example;
    Below example is to illustrate how rate limit threshold could be defined:
    Event Type – Event Type 1
    Event Type 1 Identifier –  0xD0xx
    RateLimitNr = 6
    RateLimitInterval = 10s, i.e. maximum 6 events per 10 seconds will be stored in log.
    If 10 events are received within 10s,
    4 latest events will not be logged and event type "Event Type – Event Logging Service"
    shall be reported with event code 0x06 with additional data "0xD0xx0004".

details: >
    Read any security event log record DID D048
    Set an Event in more than six times eq:10 times within 10 seconds
    Read the security log record DID D03C and check 4 latest events will not be logged
"""
import logging
import time
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_can import CanPayload
from supportfunctions.support_can import CanTestExtra

SIO = SupportFileIO
SE27 = SupportService27()
SC_CARCOM = SupportCARCOM()
SSA = SupportSecurityAccess()
SC = SupportCAN()


def security_access(dut: Dut, sa_level):
    """
    Unlock security access levels to ECU
    Args:
        dut (Dut): Dut instance
        level (str): security level
    Returns:
        Response (str): Can response
    """
    SSA.set_keys(dut.conf.default_rig_config)
    SSA.set_level_key(int(sa_level))
    payload = SSA.prepare_client_request_seed()

    response = dut.uds.generic_ecu_call(payload)
    # Prepare server response seed
    server_res_seed = response.raw[4:]
    result = SSA.process_server_response_seed(bytearray.fromhex(server_res_seed))

    payload = SSA.prepare_client_send_key()

    response = dut.uds.generic_ecu_call(payload)

    # Process server response key
    result = SSA.process_server_response_key(bytearray.fromhex(response.raw[6:(6+4)]))
    if result != 0:
        logging.error("Security access not successful")
        return False

    return True


def get_failed_event_count(dut: Dut, sa_key_read_did):
    """
    Get total number of failed event count
    Args:
        dut(Dut): An instance of Dut
        sa_key_read_did(str): Security key read DID
    Returns:
        failed_event_count(int): Failed event count
    """
    response = dut.uds.read_data_by_id_22(bytes.fromhex(sa_key_read_did))
    if response.raw[4:6] != '62':
        logging.error("Test Failed: Security key update DID is invalid or not readable")
        return None

    failed_event_count = response.data['details']['response_items'][1]['sub_payload']
    return failed_event_count


def step_1(dut: Dut):
    """
    action: Security access to ECU
    expected_result: True on successfully unlock the ECU
    """
    dut.uds.set_mode(3)
    # Security access
    sa_result = security_access(dut, sa_level='05')

    if sa_result is False:
        logging.error("Test failed: Security access denied")
        return False
    logging.info("Security access successful")
    return True


def step_2(dut: Dut, sa_key_read_did):
    """
    action: Read security key update DID and get the failed event count
    expected_result: True on successfully get failed event count
    """
    # Read current failed event count before false security key update
    event_count = get_failed_event_count(dut, sa_key_read_did)
    if event_count is not None:
        return True, event_count
    return False, None


def step_3(dut: Dut, parameters):
    """
    action: Request false security key update 'F10A' for 10 seconds consecutively
    expected_result: True on successfully increased 6 rejected events
    """
    dut.uds.set_mode(3)
    time.sleep(2)

    # Security access
    sa_result = security_access(dut, sa_level='05')

    if sa_result is False:
        logging.error("Test failed: Security access denied")
        return False

    message = parameters['sa_key_update_did'] + parameters['initial_key'] + \
              parameters['new_key'] + parameters['invalid_checksum']

    # We can't use the normal dut functions, because then "min_no_messages" and
    # "max_no_messages" is set to -1 which makes it wait longer for response.
    # We don't use dut.uds.generic_ecu_call to bypass this issue.
    payload = SC_CARCOM.can_m_send("WriteDataByIdentifier", bytes.fromhex(message), b'')
    cpay: CanPayload = {
        "payload": payload,
        "extra": ''
    }
    etp: CanTestExtra = {
        "step_no": 3,
        "purpose": '',
        "timeout": 1,
        "min_no_messages": 1,
        "max_no_messages": 1
    }
    results = []
    start_time = time.time()
    for _ in range(7):
        # Send request to ECU
        SupportTestODTB2().teststep(dut, cpay, etp)
        response = SC.can_messages[dut['receive']]

        nrc = ''
        # If not empty; Pick NRC value from position 6 to 8
        if response[0][2][6:8]:
            nrc = response[0][2][6:8]

        # Verify requestOutOfRange(NRC 31)
        if nrc == '31':
            results.append(True)
        else:
            results.append(False)

    elapsed_time = time.time() - start_time

    if len(results) != 7 or not all(results):
        logging.error("Test failed: Unable to send 7 requests consecutively or not received NRC 31"
                      " for some requests")
        return False

    if elapsed_time <= parameters['max_time']:
        logging.info("%s request sent successfully within time limit of %ss as expected",
                      len(results), parameters['max_time'])
        return True

    logging.error("Test failed: Elapsed time %ss is not less than equal to %ss", elapsed_time,
                  parameters['max_time'])
    return False


def step_4(dut: Dut, sa_key_read_did, event_count):
    """
    action: Read Security key update DID D0C1
    expected_result: True on successfully verified failed event count is increased by 6
    """
    cur_failed_event_count = int(get_failed_event_count(dut, sa_key_read_did), 16)

    # Convert hex to int
    event_count_int = int(event_count, 16)

    # Compare failed event count is increased by 6
    if cur_failed_event_count == event_count_int + 6:
        logging.info("Event count is increased by 6 as expected")
        return True

    logging.error("Test Failed: Event count not increased or flooded. expected %s, received %s",
                  event_count_int+6, cur_failed_event_count)
    return False


def run():
    """Verify Event logging rate limitation """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'sa_key_update_did': '',
                       'sa_key_read_did':'',
                       'initial_key': '',
                       'new_key': '',
                       'invalid_checksum': '',
                       'max_time': 0}
    try:
        dut.precondition(timeout=60)
        # Define did from yml file
        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameter not found")

        result_step = dut.step(step_1, purpose="Security access to ECU")
        if result_step:
            result_step, event_count = dut.step(step_2, parameters['sa_key_read_did'],
                        purpose="Read Security key update DID D0C1 and get failed event count")
        if result_step:
            result_step = dut.step(step_3, parameters,
                        purpose="Security key update consecutively for the period of 10 seconds")
        if result_step:
            result_step = dut.step(step_4, parameters['sa_key_read_did'], event_count,
                        purpose="Read Security key update DID D0C1 and verify failed event count")

        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
