"""
reqprod: 469432
version: 0
title: Security Event Header
purpose: >
    Define the structure of the Security Event Header.

description: >
    Every security event shall contain a Security Event Header, including
    • TotalNumberOfReportedEvents: The total number of reported events,
    for each individual event type.

    Figure SecurityEvent and SecurityEventHeader

    A typical read out will contain a simple header followed by all records (events).
    Notes.
    (i) If the reserved log data is not full, the TotalNumberOfReportedEvents will be identical
    to the number of stored records for a specific event type.
    (ii) A strategy for counter (TotalNumberOfReportedEvents) overflow is defined elsewhere in
    this document.
    (iii) See other requirements, defining two types of security event header.


details:
    This requirement is tested by reading the relevant DIDs. Using info in the sddb file
    it is possible to get the part of the DIDs data that belong to "TotalNumberOfReportedEvents".

    An addition to this test should be to check that the value for TotalNumberOfReportedEvents
    is correct. It could probably be done by checking the size of did_info_dics.

    There are two types of security event headers. The test accepts both.

"""
import logging

from hilding.dut import Dut
from hilding.dut import DutTestError

def __call_did(dut: Dut, did: str):

    if len(did) != 4:
        logging.error("Did id is not the correct size (should be 4)")
    res = dut.uds.read_data_by_id_22(bytes.fromhex(did))

    logging.debug("ECUs response for %s : %s",did, res)

    try:
        if res.empty() or res.data["did"] != did:
            logging.error("The response from the ECU is empty")
            return False
    except KeyError:
        logging.error("The response from the ECU does not contain the DID id (%s)",did)
        return False

    attribute_data = res.extract_from_did("Total number of reported Events")

    if not attribute_data:
        attribute_data_success = res.extract_from_did("Total number of successful events")
        attribute_data_rejected = res.extract_from_did("Total number of rejected events")
        if bool(attribute_data_success) and bool(attribute_data_rejected):
            logging.info("Security Event Header type 2:\n Data related to\
            did %s: \n\
            TotalNumberOfSuccessfulEvents: %s\n\
            TotalNumberOfRejectedEvents: %s",
            did,
            attribute_data_success,
            attribute_data_rejected)
            return True
        return False

    logging.info("Security Event Header type 1:\n\
    Data related to TotalNumberOfReportedEvents for did %s: %s",
    did,
    attribute_data)
    return True


def step_1(dut : Dut, did : str):
    """
    action:
        Test DID D046

    expected_result:
        DID read successfully and contained total number of reported events
    """
    result = __call_did(dut, did)

    logging.info("Step: %s: Result teststep: %s",
    dut.uds.step,
    result)

    return result

def step_2(dut: Dut, did : str):
    """
    action:
        Test DID D048

    expected_result:
        DID read successfully and contained total number of reported events
    """
    result = __call_did(dut, did)

    logging.info("Step: %s: Result teststep: %s",
    dut.uds.step,
    result)

    return result

def step_3(dut: Dut, did : str):
    """
    action:
        Test DID D0B7

    expected_result:
        DID read successfully and contained total number of reported events
    """
    result = __call_did(dut, did)

    logging.info("Step: %s: Result teststep: %s",
    dut.uds.step,
    result)

    return result

def step_4(dut: Dut, did : str):
    """
    action:
        Test DID D0C1

    expected_result:
        DID read successfully and contained total number of reported events
    """
    result = __call_did(dut, did)

    logging.info("Step: %s: Result teststep: %s",
    dut.uds.step,
    result)

    return result

def step_5(dut: Dut, did : str):
    """
    action:
        Test DID D03C

    expected_result:
        DID read successfully and contained total number of reported events
    """
    result = __call_did(dut, did)

    logging.info("Step: %s: Result teststep: %s",
    dut.uds.step,
    result)

    return result

def step_6(dut: Dut, did : str):
    """
    action:
        Test DID D0B8

    expected_result:
        DID read successfully and contained total number of reported events
    """
    result = __call_did(dut, did)

    logging.info("Step: %s: Result teststep: %s",
    dut.uds.step,
    result)

    return result

def step_7(dut: Dut, did : str):
    """
    action:
        Test DID D0BC

    expected_result:
        DID read successfully and contained total number of reported events
    """
    result = __call_did(dut, did)

    logging.info("Step: %s: Result teststep: %s",
    dut.uds.step,
    result)

    return result

def run():
    """
    Run - Call other functions from here

    """
    logging.warning("Script needs to be validated against working HW.")

    dut = Dut()

    start_time = dut.start()
    result = False
    try:
        # Communication with ECU lasts 60 seconds.
        dut.precondition(timeout=60)

        #List containing dids to be tested.
        dids = ["D046",
        "D048",
        "D0B7",
        "D0C1",
        "D03C",
        "D0B8",
        "D0BC"]

        dut.uds.set_mode(3)

        result = True
        result = dut.step(step_1,dids[0],
        purpose = "Test that "+dids[0]+" has the correct header") and result

        if result:
            result = dut.step(step_2,dids[1],
            purpose = "Test that "+dids[1]+" has the correct header")
        if result:
            result = dut.step(step_3,dids[2],
            purpose = "Test that "+dids[2]+" has the correct header")
        if result:
            result = dut.step(step_4,dids[3],
            purpose = "Test that "+dids[3]+" has the correct header")
        if result:
            result = dut.step(step_5,dids[4],
            purpose = "Test that "+dids[4]+" has the correct header")
        if result:
            result = dut.step(step_6,dids[5],
            purpose = "Test that "+dids[5]+" has the correct header")
        if result:
            result = dut.step(step_7,dids[6],
            purpose = "Test that "+dids[6]+" has the correct header")

    except DutTestError as error:
        logging.error("Test failed: %s", error)
        result = False
    finally:
        dut.postcondition(start_time, result)

if __name__ == '__main__':
    run()
