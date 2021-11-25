"""
reqprod: 486600
version: 0
title: Event Type - Secure Boot
purpose: >
    Define general event types that are applicable for ECUs supporting secure boot.

description: >
    Only applicable to ECUs implementing secure boot as per "LC: Secure Boot".

    The ECU shall implement event type "Secure Boot" data record with identifier 0xD0B7 as defined
     in OEM diagnostic database. Events of failed secure boot verifications shall be logged as
     defined in "Table- Secure boot Event Code".

    Event Header: SecurityEventHeaderType 1 shall be applied, i.e. using one counter. Size 32 bits.
    Event Records:
    Time. Omitted
    EventCode. As defined in "Table – Secure Boot Event Code". Size 8 bits.
    AdditionalEventData.
    For failed events, block number of the failed logical block of secure boot verification during
     ECU startup. Size 8 bits.

    Event Code    Event
    0x00    No History stored
    0x01    Failed to verify bootloader software during ECU startup
    0x02    Failed to verify application software during ECU startup
    0x03    Failed to verify operating system software during ECU startup
    0x04-0xFF    Reserved for future use or ECU specific event codes;
    Log failures if secure boot verifies additional logical blocks
    Table – Secure Boot Event Code

    Access Control: Option (3) as defined in "REQPROD 469450: Security Audit Log - Access Control"
     shall be applied.



details:
    The did is read from the ECU. It is verified that the DID is read and that the sddb
    contains header, event code and additional data.

    Further work is needed to make sure that the event codes and additional data is correct.
    To do this certain events need to be triggered and logs inspected.
"""
import logging

from hilding.dut import Dut
from hilding.dut import DutTestError

def __read_d0b7(dut):

    res = dut.uds.read_data_by_id_22(bytes.fromhex('D0B7'))

    response_items = res.details["response_items"]

    ret = {}
    ret["event_header"] = []
    ret["event_codes"] = []
    ret["additional_data"] = []

    for resp_item in response_items:
        if "Event Code" in resp_item["name"]:
            ret["event_codes"].append(resp_item)
        if "Additional Event Data" in resp_item["name"]:
            ret["additional_data"].append(resp_item)
        if "Total number of reported Events" in resp_item["name"]:
            ret["event_header"].append(resp_item)

    if len(ret["event_codes"]) != len(ret["additional_data"]) and len(ret["event_codes"]) > 0:
        logging.error("Not the same amount of event codes as additional data: %s", ret)
        raise DutTestError()

    if len(ret["event_header"]) == 0:
        logging.error("Header not found")
        raise DutTestError()

    return ret

def __evaluate_d0b7(ret):

    logging.debug(ret)

    #This function should be updated and include triggering of events etc. Dummy function for now.

    return True


def step_1(dut):
    """
    action:
        Read the did and verify its content

    expected_result:
        DID read and content is as expected according to reqprod.
    """

    ret = __read_d0b7(dut)

    return __evaluate_d0b7(ret)


def run():
    """
    Run - Call other functions from here
    """
    logging.warning("Script needs to be updated to fully cover requirement.\
 More verification of the log content is needed. One would need to trigger several events\
 to make sure the logs are correct")
    dut = Dut()

    start_time = dut.start()
    result = False
    try:
        # Communication with ECU lasts 60 seconds.
        dut.precondition(timeout=60)

        result = dut.step(step_1, purpose='Read DID D0B7')

    except DutTestError as error:
        result = False
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)

if __name__ == '__main__':
    run()
