"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



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
    It is verified that the logs for all event types contain at least 20 events.
    This is done by reading all related dids and verifying that they have at least
    20 events of one kind or at least 10 successful and 10 rejected events
"""
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError

def __test_did(dut, did, event, rej_event):
    """
    action: Read Security log event
    expected_result: Positive response with the total event records stored
    """
    res = dut.uds.read_data_by_id_22(did)
    step_result1, step_result2 = False, False
    if rej_event == 0:
        for response_item in res.data['details']['response_items']:
            if response_item['name'] == event:
                return True
        return False
    for response_item in res.data['details']['response_items']:
        if response_item['name'] == event:
            step_result1 = True
        if response_item['name'] == rej_event:
            step_result2 = True
    return step_result1 and step_result2

def step1(dut: Dut):
    """
    action: Read Security log event Security Access Application
    expected_result: Positive response with the total event records stored
    """
    return __test_did(dut, b'\xd0\x3c', "10th Latest successful event - Event Code",
        "10th Latest rejected event - Event Code")

def step2(dut: Dut):
    """
    action: Read Security log event Security Access ProgrammingSession
    expected_result: Positive response with the total event records stored
    """
    return __test_did(dut, b'\xd0\x46', "15th Latest successful event - Event Code",
        "15th Latest rejected event - Event Code")

def step3(dut: Dut):
    """
    action: Read Security log event Software Updates boot
    expected_result: Positive response with the total event records stored
    """
    return __test_did(dut, b'\xd0\x48', "10th Latest successful event - Event Code",
        "10th Latest rejected event - Event Code")

def step4(dut: Dut):
    """
    action: Read Security log event Secure Boot
    expected_result: Positive response with the total event records stored
    """
    return __test_did(dut, b'\xd0\xb7', "30th Latest event - Event Code",0)

def step5(dut: Dut):
    """
    action: Read Security log event Debugger Authentication
    expected_result: Positive response with the total event records stored
    """
    return __test_did(dut, b'\xd0\xb8', "10th Latest successful event - Event Code",
        "10th Latest rejected event - Event Code")

def step6(dut: Dut):
    """
    action: Read Security log event Secure On-Board communication
    expected_result: Positive response with the total event records stored
    """
    return __test_did(dut, b'\xd0\xbc', "24th Latest event - Event Code",0)

def step7(dut: Dut):
    """
    action: Read Security log event Security Key Updates
    expected_result: Positive response with the total event records stored
    """
    return __test_did(dut, b'\xd0\xc1', "15th Latest successful event - Event Code",
        "15th Latest rejected event - Event Code")

def run():
    """ Supporting functional requests """
    dut = Dut()
    start_time = dut.start()
    result = False
    try:
        dut.precondition()
        result1 = dut.step(step1, purpose =
        "VerificationSecurity Access Application D03C; Test that the log can store 20 event record")
        result2 = dut.step(step2, purpose =
        "Security Access ProgrammingSession D046; Test that the log can store 30 event record")
        result3 = dut.step(step3, purpose =
        "Software Updates boot D048; Test that the log can store 20 event record")
        result4 = dut.step(step4, purpose =
        "Secure Boot D0B7; Test that the log can store 30 event record")
        result5 = dut.step(step5, purpose =
        "Debugger Authentication D0B8; Test that the log can store 20 event record")
        result6 = dut.step(step6, purpose =
        "Secure On-Board communication D0BC; Test that the log can store 24 event record")
        result7 = dut.step(step7, purpose =
        "Security Key Updates D0B1; Test that the log can store 30 event record")
        result = result1 and result2 and result3 and result4 and result5 and result6 and result7

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)
if __name__ == '__main__':
    run()
