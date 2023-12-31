"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76442
version: 2
title: ReadDataByPeriodicIdentifier (2A)
purpose: >
    To make it possible to read out data with periodic transmission from ECUs.

description: >
    The ECU shall support the service readDataByPeriodicIdentifier if the ECU
    •	Is involved in propulsion or safety functions in the vehicle.
    •	Is required to implement the service due to Ethernet requirements.
    Otherwise, the ECU may support the service readDataByPeriodicIdentifier.
    If implemented, the ECU shall implement the service accordingly:

    Supported sessions-
    The ECU shall support Service readDataByPeriodicIdentifier in extendedDiagnosticSession.
    The ECU shall not support service readDataByPeriodicIdentifier in:
    •	defaultSession
    •	programmingSession
    Response time-
    Maximum response time for the service readDataByPeriodicIdentifier (0x2A) is 200 ms.

    Effect on the ECU normal operation:
    The service readDataByPeriodicIdentifier (0x2A) shall not affect the ECU’s ability to
    execute non-diagnostic tasks.

    Entry conditions-
    The ECU shall not implement entry conditions for service readDataByPeriodicIdentifier (0x2A).

    Security access-
    The ECU shall not protect service readDataByPeriodicIdentifier by using the service
    securityAccess (0x27).

details: >
    Checking response for ReadDataByPeriodicIdentifier(0x2A) in extendedDiagnosticSession with
    response code 0x6A and it should not support defaultSession and programmingSession.

    Also the maximum response time for the service ReadDataByPeriodicIdentifier(0x2A) should
    be less than 200ms.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO

SC_CARCOM = SupportCARCOM()
SIO = SupportFileIO()


def compare_positive_response(response, time_elapsed, parameters):
    """
    Compare ReadDataByPeriodicIdentifier(0x2A) positive response
    Args:
        response (str): ECU response code
        time_elapsed(int): elapsed response time
        parameters (dict): maximum response time and periodic did
    Returns:
        (bool): True on Successfully verified negative response
    """
    result = False
    if response[2:4] == '6A':
        if time_elapsed <= parameters['max_response_time']:
            logging.info("Received %s within %sms for request "
                         "ReadDataByPeriodicIdentifier(0x2A) in extended session as expected",
                         response[2:4], parameters['max_response_time'])
            result = True
        else:
            logging.error("Test failed: Time elapsed %sms is greater than %sms in extended "
                          "session", time_elapsed, parameters['max_response_time'])
            result = False
    else:
        logging.error("Test Failed: Expected positive response 6A, received %s in "
                      "extended session", response)
        result = False

    return result


def compare_negative_response(response, session):
    """
    Compare ReadDataByPeriodicIdentifier(0x2A) negative response
    Args:
        response (str): ECU response code
        session (str): diagnostic session
    Returns:
        (bool): True on Successfully verified negative response
    """
    result = False
    if response[2:4] == '7F' and response[6:8] == '7F':
        logging.info("Received NRC %s for request ReadDataByPeriodicIdentifier(0x2A)"
                        " as expected in %s session", response, session)
        result = True
    else:
        logging.error("Test Failed: Expected negative response for"
                      " ReadDataByPeriodicIdentifier(0x2A) request, received %s in %s session",
                      response, session)
        result = False
    return result


def request_read_data_periodic_identifier(dut: Dut, periodic_did):
    """
    Request ReadDataByPeriodicIdentifier(0x2A) and get the ECU response

    Args:
        dut(class object): Dut instance
        periodic_did(str): Periodic identifier did

    Returns: ECU response of ReadDataByPeriodicIdentifier request
    """

    payload = SC_CARCOM.can_m_send("ReadDataByPeriodicIdentifier", b'\x01' +
                                    bytes.fromhex(periodic_did), b'')
    response = dut.uds.generic_ecu_call(payload)

    return response.raw


def step_1(dut: Dut, parameters):
    """
    action: Set to extended mode and verify ReadDataByPeriodicIdentifier(0x2A) response

    expected_result: ECU should send positive response within 200ms
    """

    dut.uds.set_mode(3)
    # Initiate ReadDataByPeriodicIdentifier
    response = request_read_data_periodic_identifier(dut, parameters['periodic_did'])
    time_elapsed = dut.uds.milliseconds_since_request()

    result = compare_positive_response(response, time_elapsed, parameters)

    return result


def step_2(dut: Dut, periodic_did):
    """
    action: Set to default session and verify ReadDataByPeriodicIdentifier(0x2A) negative response

    expected_result: ECU should not support ReadDataByPeriodicIdentifier(0x2A) in default session
    """

    dut.uds.set_mode(1)
    # Initiate ReadDataByPeriodicIdentifier
    response = request_read_data_periodic_identifier(dut, periodic_did)
    result = compare_negative_response(response, session='default')

    return result


def step_3(dut: Dut, periodic_did):
    """
    action: Set to programming session and verify ReadDataByPeriodicIdentifier(0x2A) negative
            response

    expected_result: ECU should not support ReadDataByPeriodicIdentifier(0x2A) in
                     programming session
    """

    dut.uds.set_mode(2)
    # Initiate ReadDataByPeriodicIdentifier
    response = request_read_data_periodic_identifier(dut, periodic_did)
    result = compare_negative_response(response, session='programming')

    return result


def run():
    """
    Verify the possible to read out data with periodic transmission from ECUs withing 200ms.
    securityAccess
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False
    parameters_dict = {'max_response_time': 0,
                       'periodic_did': ''}

    try:
        dut.precondition(timeout=60)
        # Read maximum response time and periodic did from yml file
        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameter not found")

        result_step = dut.step(step_1, parameters, purpose='Verify '
                                                'ReadDataByPeriodicIdentifier(0x2A) positive '
                                                'response in extended session')
        if result_step:
            result_step = dut.step(step_2, parameters['periodic_did'], purpose='verify '
                                   'ReadDataByPeriodicIdentifier(0x2A) negative response '
                                   'in default session')
        if result_step:
            result_step = dut.step(step_3, parameters['periodic_did'], purpose='verify '
                                   'ReadDataByPeriodicIdentifier(0x2A) negative response '
                                   'in programming session')

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
