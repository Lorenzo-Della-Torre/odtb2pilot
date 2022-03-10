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
title: ReadDataByPeriodicIdentifier (2A) - transmissionMode slow (04)
purpose:
    Shall be possible to stop reading periodic identifiers without for example changing session 
    since if a session change is done a lot of other functionality might reset as well.

description: >
    The ECU shall support the service readDataByPeriodicIdentifier with the data parameter 
    transmissionMode set to stop in all sessions where the ECU supports the service 
    readDataByPeriodicIdentifier.

details: >
    1. Checking response for ReadDataByPeriodicIdentifier(0x2A) in extendedDiagnosticSession with
       response code 0x6A and it should not support defaultSession and programmingSession. 
    2. Verify transmission mode parameter slow in ReadDataByPeriodicIdentifier(0x2A) service.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO

SC_CARCOM = SupportCARCOM()
SIO = SupportFileIO()


def compare_positive_response(response, parameters, session):
    """
    Compare ReadDataByPeriodicIdentifier(0x2A) positive response
    Args:
        response (str): ECU response code
        parameters (dict): Periodic did
        session (str): diagnostic session
    Returns:
        (bool): True on Success
    """
    result = False
    if response[2:6] == parameters['periodic_did']:
        logging.info("Received %s for request "
                     "ReadDataByPeriodicIdentifier(0x2A) in %s session as expected",
                     parameters['periodic_did'], session)
        result = True
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
    Request ReadDataByPeriodicIdentifier(0x2A) with the data parameter transmissionMode set to
    stop and get the ECU response
    Args:
        dut(class object): Dut instance
        periodic_did(str): Periodic identifier did
    Returns: ECU response of ReadDataByPeriodicIdentifier request
    """

    payload = SC_CARCOM.can_m_send("ReadDataByPeriodicIdentifier", b'\x04' +
                                   bytes.fromhex(periodic_did), b'')
    response = dut.uds.generic_ecu_call(payload)

    return response.raw


def step_1(dut: Dut):
    """
    action: Set to extended mode and verify ReadDataByPeriodicIdentifier(0x2A) response  
            with transmission mode parameter set to stop.

    expected_result: ECU should send positive response
    """

    dut.uds.set_mode(3)
    # Read periodic did from yml file
    parameters_dict = {'periodic_did': ''}
    parameters = SIO.parameter_adopt_teststep(parameters_dict)
    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False, None

    # Initiate ReadDataByPeriodicIdentifier
    response = request_read_data_periodic_identifier(dut, parameters['periodic_did'])

    result = compare_positive_response(response, parameters, 'extended')

    return result, parameters


def step_2(dut: Dut, periodic_did):
    """
    action: Set to default session and verify ReadDataByPeriodicIdentifier(0x2A) negative response
            with transmission mode parameter set to stop.

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
            response with transmission mode parameter set to stop.

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
    Verify transmissionMode parameter stop 0x04 in ReadDataByPeriodicIdentifier(0x2A) service
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=60)
        result_step, parameters = dut.step(step_1, purpose='Verify '
                                           'ReadDataByPeriodicIdentifier(0x2A) response '
                                           'in extended session with the transmissionMode'
                                           'parameter set to stop')
        if result_step:
            result_step = dut.step(step_2, parameters['periodic_did'], purpose='verify '
                                   'ReadDataByPeriodicIdentifier(0x2A) negative response '
                                   'in default session with the transmissionMode '
                                   'parameter set to stop')
        if result_step:
            result_step = dut.step(step_3, parameters['periodic_did'], purpose='verify '
                                   'ReadDataByPeriodicIdentifier(0x2A) negative response '
                                   'in programming session with the transmissionMode '
                                   'parameter set to stop')

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
