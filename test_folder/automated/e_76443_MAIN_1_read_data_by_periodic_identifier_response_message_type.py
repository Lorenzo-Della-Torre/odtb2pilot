"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76443
version: 1
title: ReadDataByPeriodicIdentifier (2A) - response message type
purpose: >
    Define one method to be used for all periodic identifiers

description: >
    The ECU shall only support response message type #2. See also “ISO 14229-1:2013
    road vehicles -- unified diagnostic services (UDS) -- part 1: specification and requirements”
    for a detailed description of response message type #2.

details: >
    Implement a method for response message type #2 and verify the response of
    ReadDataByPeriodicIdentifier(0x2A) in extendedDiagnosticSession with response code 0x6A.
"""

import logging
import time
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_can import SupportCAN

SC_CARCOM = SupportCARCOM()
SIO = SupportFileIO()
SC = SupportCAN()


def get_response(dut, periodic_did):
    """
    Get response of periodic did and verify with ReadDataByPeriodicIdentifier(0x2A)
    positive response
    Args:
        dut (Dut): An instance of Dut
        periodic_did (str): periodic_did
    Returns:
        (bool): True on successfully verified positive response
    """
    while True:
        # Wait for 10ms
        time.sleep(10/1000)
        response = SC.can_messages[dut["receive"]][0][2]
        if response[2:4] == periodic_did:
            logging.info("Periodic message %s received with type 2 structure as expected", response)
            return True
        logging.error("Response received %s doesn't comply with Type 2", response)
        return False


def verify_positive_response(dut, periodic_did):
    """
    Verify ReadDataByPeriodicIdentifier(0x2A) positive response of type2
    with response code 0x6A
    Args:
        dut(Dut): Dut instance
        periodic_did (str): periodic_did
    Returns:
        (bool): True on successfully verified positive response
    """
    result = get_response(dut, periodic_did)

    if result:
        logging.info("Received periodic message for periodic DID in extended session"
                     " as expected")
        return True

    logging.error("Expected periodic message for periodic DID in extended session,"
                  " received unexpected message Type")
    return False


def request_read_data_periodic_identifier(dut: Dut, periodic_did):
    """
    Request ReadDataByPeriodicIdentifier(0x2A) and get the ECU response
    Args:
        dut(class object): Dut instance
        periodic_did(str): Periodic did
    Returns:
        response.raw(str): ECU response
    """
    payload = SC_CARCOM.can_m_send("ReadDataByPeriodicIdentifier", b'\x01' +
                                    bytes.fromhex(periodic_did), b'')
    # Check response message type #2
    response = dut.uds.generic_ecu_call(payload)

    return response.raw


def step_1(dut: Dut):
    """
    action: Set to extended mode and verify message type #2 response for
            ReadDataByPeriodicIdentifier(0x2A).
    expected_result: ECU should send positive response
    """
    dut.uds.set_mode(3)
    # Read maximum response time and periodic did from yml file
    parameters_dict = {'periodic_did': ''}
    parameters = SIO.parameter_adopt_teststep(parameters_dict)
    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False

    # Initiate ReadDataByPeriodicIdentifier
    response = request_read_data_periodic_identifier(dut, parameters['periodic_did'])
    if response[2:4] != '6A':
        logging.error("Test Failed: Initial response verification failed")
        return False
    logging.info("-----Initial response verified successfully-----")

    # Start verifying periodic response
    result = verify_positive_response(dut, parameters['periodic_did'])

    # Send a request to stop reading periodic identifier did
    payload = SC_CARCOM.can_m_send("ReadDataByPeriodicIdentifier", b'\x04'
                                  + bytes.fromhex(parameters['periodic_did']), b'')
    dut.uds.generic_ecu_call(payload)

    if result:
        logging.info("Successfully verified positive response for periodic DID in "
                     "extended session with transmissionMode slow")
        return True
    logging.error("Test Failed: Received unexpected response for periodic DID")
    return False


def run():
    """
    Check response for ReadDataByPeriodicIdentifier(0x2A) in extendedDiagnosticSession with
    response code 0x6A for implemented response message type #2.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    try:
        dut.precondition(timeout=60)

        result = dut.step(step_1, purpose='Set to extended mode and verify message type#2 '
                              'response ReadDataByPeriodicIdentifier(0x2A)')

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
