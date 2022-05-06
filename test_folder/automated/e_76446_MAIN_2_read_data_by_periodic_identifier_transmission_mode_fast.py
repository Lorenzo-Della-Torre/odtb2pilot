"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76446
version: 2
title: ReadDataByPeriodicIdentifier (2A) - transmissionMode fast (03)
purpose: >
    Define the transmissionMode fast

description: >
    The ECU may support the service readDataByPeriodicIdentifier with the data parameter
    transmissionMode set to fast in all sessions where the ECU supports the service
    readDataByPeriodicIdentifier. The implementer defines the value of the transmission rate
    in the transmissionMode fast. The transmissionMode fast is allowed to be defined as "as fast
    as possible" i.e. must not be fixed, it may change over time (e.g. be CPU load dependent).

details: >
    Verify ECU response for ReadDataByPeriodicIdentifier(0x2A) service in
    extendedDiagnosticSession with response code 0x6A with transmission mode fast rate (0x03)
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
    Get response within defined time period for fast rate(25ms) and verify
    ReadDataByPeriodicIdentifier(0x2A) positive response
    Args:
        dut (Dut): An instance of Dut
        parameters (dict): periodic_did, fast_rate_max_time
    Returns:
        (bool): True on successfully verified positive response
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
        if elapsed_time * 1000 >= parameters['fast_rate_max_time']*2:
            result = False
            logging.error("Periodic message not received")
            break
    # Calculate tolerance (10%)
    tolerance = int((10/parameters['fast_rate_max_time'])*100)
    # Convert elapsed_time to millisecond
    elapsed_time = int(elapsed_time*1000)
    fast_threshold_time_min = parameters['fast_rate_max_time'] - tolerance
    fast_threshold_time_max = parameters['fast_rate_max_time'] + tolerance

    fast_threshold_time_min_result = elapsed_time >= fast_threshold_time_min
    fast_threshold_time_max_result = elapsed_time <= fast_threshold_time_max
    # Compare response time
    if result and fast_threshold_time_min_result and fast_threshold_time_max_result:
        logging.info("Positive response %s received as expected within %s and %s time",
                     response[4:6], fast_threshold_time_min, fast_threshold_time_max)
        return True

    logging.error("Response received %s, expected %s within %s and %s", response[4:6],
                  parameters['periodic_did'], fast_threshold_time_min, fast_threshold_time_max)
    return False


def verify_positive_response(dut, parameters):
    """
    Verify ReadDataByPeriodicIdentifier(0x2A) positive response 0x6A
    Args:
        dut(Dut): Dut instance
        parameters (dict): periodic_did, fast_rate_max_time
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
    Request ReadDataByPeriodicIdentifier(0x2A) with transmission mode fast rate 0x03 and
    get the ECU response
    Args:
        dut(Dut): Dut instance
        periodic_did(str): Periodic identifier did
    """
    # Request periodic did with transmissionMode fast rate
    payload = SC_CARCOM.can_m_send("ReadDataByPeriodicIdentifier", b'\x03' +
                                    bytes.fromhex(periodic_did), b'')
    response = dut.uds.generic_ecu_call(payload)
    return response.raw


def step_1(dut: Dut, parameters):
    """
    action: Set to extended mode and verify ReadDataByPeriodicIdentifier(0x2A) response
            with transmissionMode fast rate 0x03
    expected_result: ECU should send positive response 0x6A
    """
    dut.uds.set_mode(3)

    # Initiate ReadDataByPeriodicIdentifier
    response = request_read_data_periodic_identifier(dut, parameters['periodic_did'])
    if response[2:4] != '6A':
        logging.error("Test Failed: Initial response verification failed")
        return False

    logging.info("-----Initial response verified successfully-----")
    # Start verifying periodic response
    result = verify_positive_response(dut, parameters)

    # Stop dynamically defined periodic DID
    payload = SC_CARCOM.can_m_send("ReadDataByPeriodicIdentifier", b'\x04'
                                   + bytes.fromhex(parameters['periodic_did']), b'')
    dut.uds.generic_ecu_call(payload)

    if result:
        logging.info("Successfully verified positive response for periodic DIDs in "
                     "extended session with transmissionMode fast 0x03")
        return True
    logging.error("Test Failed: Received unexpected response for one or more periodic DIDs")
    return False


def run():
    """
    Verify ECU response of ReadDataByPeriodicIdentifier(0x2A) service with transmission mode
    set to fast(0x03)
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    parameters_dict = {'periodic_did': '',
                       'fast_rate_max_time': 0}

    try:
        dut.precondition(timeout=60)
        # Read periodic did from yml file
        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameter not found")

        result = dut.step(step_1, parameters, purpose='Verify '
                                              'ReadDataByPeriodicIdentifier(0x2A) response '
                                              'with transmissionMode fast in extended session')
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
