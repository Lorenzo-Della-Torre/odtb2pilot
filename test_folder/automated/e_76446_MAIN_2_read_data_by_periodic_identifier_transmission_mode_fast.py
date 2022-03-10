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
    1. Checking response for ReadDataByPeriodicIdentifier(0x2A) in extendedDiagnosticSession with
    response code 0x6A and it should not support defaultSession and programmingSession. Also the
    maximum response time for the service ReadDataByPeriodicIdentifier(0x2A) should be
    less than 200ms.
    2. Verify transmission mode fast parameter in ReadDataByPeriodicIdentifier(0x2A) service.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.conf import Conf
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO

CNF = Conf()
SC_CARCOM = SupportCARCOM()
SE27 = SupportService27()
SIO = SupportFileIO()


def compare_positive_response(response, time_elapsed, parameters, session):
    """
    Compare ReadDataByPeriodicIdentifier(0x2A) positive response
    Args:
        response (str): ECU response code
        time_elapsed(int): elapsed response time
        parameters (dict): maximum response time and periodic did
        session (str): diagnostic session
    Returns:
        (bool): True on Success
    """
    result = False
    if response[2:6] == parameters['periodic_did']:
        if time_elapsed <= parameters['max_response_time']:
            logging.info("Received %s within %sms for request "
                         "ReadDataByPeriodicIdentifier(0x2A) in %s session as expected",
                         parameters['periodic_did'], parameters['max_response_time'], session)
            result = True
        else:
            logging.error("Test failed: Time elapsed %sms is greater than %sms in %s",
                          time_elapsed, parameters['max_response_time'], session)
            result = False
    else:
        logging.error("Test Failed: Expected positive response %s, received %s in %s session",
                      parameters['periodic_did'], response, session)
        result = False

    return result


def compare_negative_response(response, session):
    """
    Compare ReadDataByPeriodicIdentifier(0x2A) negative response
    Args:
        response (str): ECU response code
        session (str): diagnostic session
    Returns:
        (bool): True on Success
    """
    result = False
    if response[2:4] == '7F' and response[6:8] == '11':
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
    Request ReadDataByPeriodicIdentifier(0x2A) with transmission mode fast parameter and
    get the ECU response
    Args:
        dut(class object): Dut instance
        periodic_did(str): Periodic identifier did
    Returns: ECU response of ReadDataByPeriodicIdentifier request
    """
    # Request periodic did with transmission mode fast parameter 0x03
    payload = SC_CARCOM.can_m_send("ReadDataByPeriodicIdentifier", b'\x03' +
                                    bytes.fromhex(periodic_did), b'')
    response = dut.uds.generic_ecu_call(payload)

    return response.raw


def step_1(dut: Dut):
    """
    action: Set to extended mode and verify ReadDataByPeriodicIdentifier(0x2A) response
            with transmission mode fast parameter.
    expected_result: ECU should send positive response within 200ms
    """
    dut.uds.set_mode(3)
    # Read maximum response time and periodic did from yml file
    parameters_dict = {'max_response_time': 0,
                       'periodic_did': ''}
    parameters = SIO.parameter_adopt_teststep(parameters_dict)
    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False, None

    # Initiate ReadDataByPeriodicIdentifier
    response = request_read_data_periodic_identifier(dut, parameters['periodic_did'])
    time_elapsed = dut.uds.milliseconds_since_request()

    result = compare_positive_response(response, time_elapsed, parameters, 'extended')

    return result, parameters


def step_2(dut: Dut, periodic_did):
    """
    action: Set to default session and verify ReadDataByPeriodicIdentifier(0x2A) negative response
            with transmission mode fast parameter.
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
            response with transmission mode fast parameter.
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
    Verify transmission mode fast parameter in ReadDataByPeriodicIdentifier(0x2A) service
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=60)
        result_step, parameters = dut.step(step_1, purpose='Verify '
                                                  'ReadDataByPeriodicIdentifier(0x2A) response '
                                                 'with transmission mode fast in extended session')
        if result_step:
            result_step = dut.step(step_2, parameters['periodic_did'], purpose='verify '
                                   'ReadDataByPeriodicIdentifier(0x2A) negative response '
                                   'with transmission mode fast in default session')
        if result_step:
            result_step = dut.step(step_3, parameters['periodic_did'], purpose='verify '
                                   'ReadDataByPeriodicIdentifier(0x2A) negative response '
                                   'with transmission mode fast in programming session')

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
