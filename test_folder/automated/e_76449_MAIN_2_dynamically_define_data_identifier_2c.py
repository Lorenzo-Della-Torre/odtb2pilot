"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76449
version: 2
title: DynamicallyDefineDataIdentifier (2C)
purpose: >
    In some cases DynamicallyDefineDataIdentifiers is used for testing the ECUs

description: >
    The ECU shall support the service dynamicallyDefineDataIdentifier if the ECU:
        => Is involved in propulsion or safety functions in the vehicle.
        => Is required to implement the service due to Ethernet requirements.
    Otherwise, the ECU may support the service dynamicallyDefineDataIdentifier.
    If implemented, the ECU shall implement the service accordingly:

    Supported sessions:
    The ECU shall support Service dynamicallyDefineDataIdentifier in:
        => defaultSession
        => extendedDiagnosticSession
    The ECU shall not support service dynamicallyDefineDataIdentifier in programmingSession.

    Response time:
    Maximum response time for the service dynamicallyDefineDataIdentifier (0x2C) is 200 ms.

    Effect on the ECU normal operation:
    The service dynamicallyDefineDataIdentifier (0x2C) shall not affect the ECU's ability to
    execute non-diagnostic tasks.

    Entry conditions:
    The ECU shall not implement entry conditions for service dynamicallyDefineDataIdentifier(0x2C).

    Security access:
    The ECU may protect service dynamicallyDefineDataIdentifier by using the service
    securityAccess (0x27). If data that is read by service readDataByIdentifier (0x22) or
    readMemoryByAddress (0x23) is protected by security access, then the service shall be protected
    by security access when including this same data (completely or partly) in the dynamically
    defined dataIdentifier.

details: >
    Verify response for dynamicallyDefineDataIdentifier(0x2C) in default & extended session with
    response code 0x6C and it should not support in programming session.
    Also the maximum response time for the service dynamicallyDefineDataIdentifier(0x2C) should
    be less than 200ms.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO

SC_CARCOM = SupportCARCOM()
SIO = SupportFileIO()


def compare_positive_response_clear(response, define_did, session):
    """
    Compare dynamicallyDefineDataIdentifier(0x2C) - clear of dynamicallyDefineDataIdentifier
    positive response
    Args:
        response (str): ECU response code
        define_did (str): Dynamically define did
        session (str): Diagnostic session
    Returns:
        (bool): True on successfully verified positive response
    """
    result = False

    if response[2:4] == '6C' and response[6:10] == define_did:
        logging.info("Received %s for request dynamicallyDefineDataIdentifier(0x2C) - "
                     "clear of dynamicallyDefineDataIdentifier in %s session as expected",
                      define_did, session)
        result = True
    else:
        logging.error("Test Failed: Expected positive response %s, received %s in %s session",
                       define_did, response, session)
        result = False

    return result


def clear_dynamically_define_data_identifier(dut, define_did):
    """
    Initiate dynamicallyDefineDataIdentifier(0x2C) - clear of dynamicallyDefineDataIdentifier
    request
    Args:
        dut (Dut): An instance of Dut
        define_did (str): Dynamically defined did
    Returns:
        response (str): ECU response code
    """
    payload = SC_CARCOM.can_m_send("DynamicallyDefineDataIdentifier", b'\x03'
                                   + bytes.fromhex(define_did)
                                   , b'')
    response = dut.uds.generic_ecu_call(payload)
    return response.raw


def compare_positive_response(response, time_elapsed, parameters, session):
    """
    Compare dynamicallyDefineDataIdentifier(0x2C) positive response
    Args:
        response (str): ECU response code
        time_elapsed (int): Response time
        parameters (dict): Maximum response time and define did
        session (str): Diagnostic session
    Returns:
        (bool): True when received positive response '6C'
    """
    result = False
    if response[2:4] == '6C' and response[6:10] == parameters['define_did']:
        if time_elapsed <= parameters['max_response_time']:
            logging.info("Received %s within %sms for request "
                         "dynamicallyDefineDataIdentifier(0x2C) in %s session as expected",
                          parameters['define_did'], parameters['max_response_time'], session)
            result = True
        else:
            logging.error("Test Failed: Time elapsed %sms is greater than %sms in %s session",
                          time_elapsed, parameters['max_response_time'], session)
            result = False
    else:
        logging.error("Test Failed: Expected positive response %s, received %s in %s session",
                       parameters['define_did'], response, session)
        result = False

    return result


def compare_negative_response(response, session, nrc_code):
    """
    Compare dynamicallyDefineDataIdentifier(0x2C) negative response
    Args:
        response (str): ECU response code
        session (str): Diagnostic session
        nrc_code (str): Negative response code
    Returns:
        (bool): True when received negative response '7F'
    """
    result = False
    if response[2:4] == '7F' and response[6:8] == nrc_code:
        logging.info("Received NRC %s for request dynamicallyDefineDataIdentifier(0x2C) in %s"
                     " session as expected", response[6:8], session)
        result = True
    else:
        logging.error("Test Failed: Expected NRC %s for request"
                      " dynamicallyDefineDataIdentifier(0x2C) in %s session, received %s",
                        nrc_code, session, response)
        result = False

    return result


def dynamically_define_data_identifier(dut, parameters):
    """
    Initiate dynamicallyDefineDataIdentifier(0x2C) request
    Args:
        dut (Dut): An instance of Dut
        parameters (dict): yml parameters
    Returns:
        response (str): ECU response code
    """
    payload = SC_CARCOM.can_m_send("DynamicallyDefineDataIdentifier", b'\x01'
                                   + bytes.fromhex(parameters['define_did'])
                                   + bytes.fromhex(parameters['source_data_identifier'])
                                   + bytes.fromhex(parameters['position_in_source_data_record'])
                                   + bytes.fromhex(parameters['memory_size'])
                                   , b'')
    response = dut.uds.generic_ecu_call(payload)
    return response.raw


def step_1(dut: Dut, parameters):
    """
    action: Verify dynamicallyDefineDataIdentifier(0x2C) request in default session
    expected_result: ECU should send positive response within 200ms
    """
    # Initiate DynamicallyDefineDataIdentifier
    response = dynamically_define_data_identifier(dut, parameters)
    time_elapsed = dut.uds.milliseconds_since_request()

    return compare_positive_response(response, time_elapsed, parameters, session='default')


def step_2(dut: Dut, parameters):
    """
    action: Verify dynamicallyDefineDataIdentifier(0x2C) in programming session
    expected_result: ECU should not support dynamicallyDefineDataIdentifier(0x2C)
                     in programming session
    """
    # Change to programming session
    dut.uds.set_mode(2)

    # Initiate DynamicallyDefineDataIdentifier
    response = dynamically_define_data_identifier(dut, parameters)
    return compare_negative_response(response, session='programming', nrc_code='11')


def step_3(dut: Dut, parameters):
    """
    action: Verify dynamicallyDefineDataIdentifier(0x2C) request in extended session
    expected_result: ECU should send positive response within 200ms
    """
    # Change to extended session
    dut.uds.set_mode(1)
    dut.uds.set_mode(3)

    # Initiate DynamicallyDefineDataIdentifier
    response = dynamically_define_data_identifier(dut, parameters)
    time_elapsed = dut.uds.milliseconds_since_request()
    return compare_positive_response(response, time_elapsed, parameters, session='extended')


def step_4(dut: Dut, define_did):
    """
    action: Clear dynamicallyDefineDataIdentifier
    expected_result: ECU should give positive response for request
                     dynamicallyDefineDataIdentifier(0x2C) - clear of
                     dynamicallyDefineDataIdentifier
    """
    # DynamicallyDefineDataIdentifier (2C)-clear of dynamicallyDefineDataIdentifier
    response = clear_dynamically_define_data_identifier(dut, define_did)
    return compare_positive_response_clear(response, define_did, session='Extended')


def run():
    """
    Verify response for dynamicallyDefineDataIdentifier(0x2C) in default & extended session with
    response code 0x6C and it should not support in programming session.
    Also the maximum response time for the service dynamicallyDefineDataIdentifier(0x2C) should
    be less than 200ms.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'max_response_time': 0,
                       'define_did': '',
                       'source_data_identifier':'',
                       'position_in_source_data_record':'',
                       'memory_size':''}
    try:
        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        dut.precondition(timeout=60)

        result_step = dut.step(step_1, parameters, purpose='Verify '
                              'dynamicallyDefineDataIdentifier(0x2C) response in default session')
        if result_step:
            result_step = dut.step(step_2, parameters, purpose='Verify'
                                  ' dynamicallyDefineDataIdentifier(0x2C) negative response in'
                                  ' programming session')
        if result_step:
            result_step = dut.step(step_3, parameters, purpose='Verify '
                                  'dynamicallyDefineDataIdentifier(0x2C) response in extended'
                                  ' session')
        if result_step:
            result_step = dut.step(step_4, parameters['define_did'], purpose='Clear'
                                  ' dynamicallyDefineDataIdentifier')
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
