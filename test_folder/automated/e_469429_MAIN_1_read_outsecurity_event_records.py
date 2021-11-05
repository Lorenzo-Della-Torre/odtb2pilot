"""
reqprod: 469429
version: 1
title: Read Out Security Event records
purpose: >
    Define how to read log using a diagnostic client. A typical use-case is to read the information
     while ECU application is running, i.e. without forcing the vehicle into programming session
    (convenience).

description: >
    It shall be possible to read all Security Event types via the diagnostic protocol,
     using the service ReadDataByIdentifier. Event types reported in programmingSession
      shall also be available to read in non-programmingSession.

    A unique DID shall be applied for each type.


details:
    From an excel sheet attached to the Vira story the different events are obtained.
    Each of the events has a DID connected to it, these DIDs are read to verify that

    "It shall be possible to read all Security Event types via the diagnostic protocol,
     using the service ReadDataByIdentifier."

    A check is also done to make sure that the sizes of the DIDs are correct.
    This increases the likelyhood that the DID is correct.
"""
import logging

from hilding.dut import Dut
from hilding.dut import DutTestError


def __call_did(dut: Dut, did: str, did_size):

    if len(did) != 4:
        logging.error("Did id is not the correct size (should be 4)")
    res = dut.uds.read_data_by_id_22(bytes.fromhex(did))

    logging.info("ECUs response for %s : %s",did, res)

    try:
        if res.empty() or not res.data["did"] == str:
            logging.error("The response from the ECU is empty")
            return False
    except KeyError:
        logging.error("The response from the ECU does not contain the DID id (%s)",did)
        return False

    try:
        if res.data["size"] != did_size:
            logging.error("The response has the wrong size, %s insted of %s",
            res.data["size"],
            did_size)
            return False
        logging.info("DID %s has the correct size", did)
        return True
    except KeyError:
        logging.error("The response from the ECU does not contain info about the DIDs size")
        return False


def step_1(dut : Dut, did : str, did_size):
    """
    action:
        Test DID D046

    expected_result:
        DID read successfully
    """
    return __call_did(dut, did, did_size)

def step_2(dut: Dut, did : str, did_size):
    """
    action:
        Test DID D048

    expected_result:
        DID read successfully
    """
    return __call_did(dut, did, did_size)

def step_3(dut: Dut, did : str, did_size):
    """
    action:
        Test DID D0B7

    expected_result:
        DID read successfully
    """
    return __call_did(dut, did, did_size)

def step_4(dut: Dut, did : str, did_size):
    """
    action:
        Test DID D0C1

    expected_result:
        DID read successfully
    """
    return __call_did(dut, did, did_size)

def step_5(dut: Dut, did : str, did_size):
    """
    action:
        Test DID D03C

    expected_result:
        DID read successfully
    """
    return __call_did(dut, did, did_size)

def step_6(dut: Dut, did : str, did_size):
    """
    action:
        Test DID D0B8

    expected_result:
        DID read successfully
    """
    return __call_did(dut, did, did_size)

def step_7(dut: Dut, did : str, did_size):
    """
    action:
        Test DID D0BC

    expected_result:
        DID read successfully
    """
    return __call_did(dut, did, did_size)

def run():
    """
    Run - Call other functions from here

    """
    dut = Dut()

    start_time = dut.start()
    result = False
    try:
        # Communication with ECU lasts 60 seconds.
        dut.precondition(timeout=60)

        #Dictionary containing dids to be tested.
        #
        #Also contains size (in bytes) to verify that the content has correct size.
        app_did_dict = dut.conf.rig.sddb_dids["app_did_dict"]

        did_dict = {"D046" : app_did_dict['D046']["size"],
        "D048" : app_did_dict["D048"]["size"],
        "D0B7" : app_did_dict["D0B7"]["size"],
        "D0C1" : app_did_dict["D0C1"]["size"],
        "D03C" : app_did_dict["D03C"]["size"],
        "D0B8" : app_did_dict["D0B8"]["size"],
        "D0BC" : app_did_dict["D0BC"]["size"]}

        result = True
        for i,did in enumerate(did_dict):
            result = dut.step(globals()["step_"+str(i+1)],
            did,
            did_dict[did],
            purpose="Test that " + did + " works as intended") and result
    except DutTestError as error:
        logging.error("Test failed: %s", error)
        result = False
    except KeyError as error:
        logging.error("Test failed since DID is not in sddb file: %s", error)
        result = False
    finally:
        dut.postcondition(start_time, result)

if __name__ == '__main__':
    run()
