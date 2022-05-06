"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76444
version: 1
title: ReadDataByPeriodicIdentifier (2A) - transmissionMode slow (01)
purpose: >
    Define the transmissionMode slow

description: >
    The ECU may support the service readDataByPeriodicIdentifier with the data parameter
    transmissionMode slow in all sessions where the ECU supports the service
    readDataByPeriodicIdentifier. The implementer defines the value of the transmission rate
    in the transmissionMode slow.

details: >
    Verify ECU response for ReadDataByPeriodicIdentifier(0x2A) service in
    extendedDiagnosticSession with response code 0x6A with transmission mode fast slow (0x01)
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


def get_response(dut, parameters):
    """
    Get response within defined time period for slow rate(600ms) and verify
    ReadDataByPeriodicIdentifier(0x2A) positive response
    Args:
        dut (Dut): An instance of Dut
        parameters (dict): periodic_did, slow_rate_max_time
    Returns:
        (bool): True on successfully verified positive periodic response
    """

    start_time = SC.can_messages[dut["receive"]][0][0]
    result = False
    while True:
        # Wait for 10ms
        time.sleep(10/1000)
        response = SC.can_messages[dut["receive"]][0][2]
        receive_time = SC.can_messages[dut["receive"]][0][0]
        elapsed_time = receive_time - start_time
        if response[2:4] == parameters['periodic_did']:
            result = True
            break
        if elapsed_time * 1000 >= parameters['slow_rate_max_time']*2:
            result = False
            logging.error("Periodic message not received")
            break
    # Calculate tolerance (10%)
    tolerance = int((10/parameters['slow_rate_max_time'])*100)
    # Convert elapsed_time to millisecond
    elapsed_time = int(elapsed_time*1000)
    slow_threshold_time_min = parameters['slow_rate_max_time'] - tolerance
    slow_threshold_time_max = parameters['slow_rate_max_time'] + tolerance

    slow_threshold_time_min_result = elapsed_time >= slow_threshold_time_min
    slow_threshold_time_max_result = elapsed_time <= slow_threshold_time_max
    # Compare response time
    if result and slow_threshold_time_min_result and slow_threshold_time_max_result:
        logging.info("Positive response %s received as expected witin %s and %s time",
                     response[4:6], slow_threshold_time_min, slow_threshold_time_max)
        return True

    logging.error("Response received %s, expected %s within %s and %s", response[4:6],
                  parameters['periodic_did'], slow_threshold_time_min, slow_threshold_time_max)
    return False


def verify_positive_response(dut, parameters):
    """
    Verify ReadDataByPeriodicIdentifier(0x2A) positive response 0x6A
    Args:
        dut (Dut): An instance of Dut
        parameters (dict): periodic_did, slow_rate_max_time
    Returns:
        (bool): True on successfully verified positive response
    """

    result = get_response(dut, parameters)

    if result:
        logging.info("Received positive response for periodic DID in extended session"
                     " as expected")
        return True

    logging.error("Expected positive response for periodic DID in extended session,"
                  " received unexpected response")
    return False


def request_read_data_periodic_identifier(dut: Dut, periodic_did):
    """
    Request ReadDataByPeriodicIdentifier(0x2A) with transmission mode slow parameter 0x01 and
    get the ECU response.
    Args:
        dut(class object): Dut instance
        periodic_did(str): Periodic identifier did
    Returns:
        response.raw(str): ECU response
    """
    # Request periodic dids with transmissionMode slow rate
    payload = SC_CARCOM.can_m_send("ReadDataByPeriodicIdentifier", b'\x01' +
                                    bytes.fromhex(periodic_did), b'')
    response = dut.uds.generic_ecu_call(payload)
    return response.raw


def step_1(dut: Dut):
    """
    action: Set to extended mode and verify ReadDataByPeriodicIdentifier(0x2A) response
            with transmissionMode slow rate 0x01
    expected_result: ECU should send positive response 0x6A and periodic message as per slow
            rate defined.
    """
    dut.uds.set_mode(3)
    # Read did from yml file
    parameters_dict = {'periodic_did': '',
                       'slow_rate_max_time': 0}
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
    result = verify_positive_response(dut, parameters)

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
    Verify ECU response of ReadDataByPeriodicIdentifier(0x2A) service with transmission mode
    set to slow(0x01)
    """
    dut = Dut()

    start_time = dut.start()
    result = False

    try:
        dut.precondition(timeout=60)

        result = dut.step(step_1, purpose='Verify ReadDataByPeriodicIdentifier(0x2A) response '
                          'with transmissionMode slow in extended session')
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
