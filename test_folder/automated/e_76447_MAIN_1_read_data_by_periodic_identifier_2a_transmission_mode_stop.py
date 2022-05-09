"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76447
version: 1
title: ReadDataByPeriodicIdentifier (2A) - transmissionMode stop (04)
purpose:
    Shall be possible to stop reading periodic identifiers without for example changing session
    since if a session change is done a lot of other functionality might reset as well.

description: >
    The ECU shall support the service readDataByPeriodicIdentifier with the data parameter
    transmissionMode set to stop in all sessions where the ECU supports the service
    readDataByPeriodicIdentifier.

details: >
    Verify ECU stop sending periodic response with readDataByPeriodicIdentifier(2A) service
    1. Start readDataByPeriodicIdentifier(2A) with transmissionMode fast
    2. Verify whether ECU started sending periodic response
    3. Send transmission mode stop request and verify ECU stop sending periodic response
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


def verify_periodic_response(dut, parameters):
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


def verify_initial_response(response, periodic_did):
    """
    Verify ReadDataByPeriodicIdentifier(0x2A) positive response
    Args:
        response (str): ECU response code
        periodic_did (str): Periodic did
    Returns:
        (bool): True on Successfully verified positive response
    """
    result = False
    if response[2:4] == '6A':
        logging.info("Received %s for request ReadDataByPeriodicIdentifier(0x2A) in extended "
                     "session as expected", response[2:4])
        result = True
    else:
        logging.error("Test Failed: Expected positive response %s, received %s in extended "
                      "session", periodic_did, response)
        result = False

    return result


def request_read_data_periodic_identifier(dut: Dut, periodic_did, transmission_mode):
    """
    Request ReadDataByPeriodicIdentifier(0x2A) with the transmissionMode to the ECU response
    Args:
        dut(Dut): Dut instance
        periodic_did(str): Periodic identifier did
        transmission_mode(str): Periodic transmission mode
    Returns:
        response.raw (str): ECU response of ReadDataByPeriodicIdentifier request
    """

    payload = SC_CARCOM.can_m_send("ReadDataByPeriodicIdentifier", bytes.fromhex(transmission_mode)
                                   + bytes.fromhex(periodic_did), b'')
    response = dut.uds.generic_ecu_call(payload)

    return response.raw


def step_1(dut: Dut, parameters):
    """
    action: Set to extended session and verify ReadDataByPeriodicIdentifier(0x2A)
            is stop sending response.
    expected_result: True when ReadDataByPeriodicIdentifier(0x2A) response 6A verified successfully
                     for TransmissionModeStop(04)
    """

    dut.uds.set_mode(3)

    # Initiate ReadDataByPeriodicIdentifier
    response = request_read_data_periodic_identifier(dut, parameters['periodic_did'],
                                                     transmission_mode='03')
    # Verify initial period response for transmission mode fast
    result = verify_initial_response(response, parameters['periodic_did'])
    # Start verifying periodic response
    periodic_result = result and verify_periodic_response(dut, parameters)
    time.sleep(5)

    if periodic_result:
        logging.error("Test Failed: ReadDataByPeriodicIdentifier(2A) service not started")
        return False
    # Send a request to stop periodic response
    response = request_read_data_periodic_identifier(dut, parameters['periodic_did'],
                                                    transmission_mode='04')
    # Verify initial period response for transmission mode stop
    result = verify_initial_response(response, parameters['periodic_did'])

    return result


def run():
    """
    Verify transmissionMode stop 0x04 in ReadDataByPeriodicIdentifier(0x2A) service
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    parameters_dict = {'periodic_did': '',
                       'fast_rate_max_time': ''}

    try:
        dut.precondition(timeout=60)
        # Read periodic did from yml file
        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameter not found")

        result = dut.step(step_1, parameters, purpose='Verify ReadDataByPeriodicIdentifier(0x2A)'
                          'response in extended session with the transmissionMode set to stop')

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
