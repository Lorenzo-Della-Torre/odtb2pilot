"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76450
version: 1
title: DynamicallyDefineDataIdentifier (2C) - defineByIdentifier (01, 81)
purpose: >
    Compliance with VOLVO CAR CORPORATION tools.

description: >
    The ECU may support the service dynamicallyDefineDataIdentifier - defineByIdentifier in all
    sessions where the ECU supports the service dynamicallyDefineDataIdentifier.

details: >
    Verify ECU may support the service dynamicallyDefineDataIdentifier - defineByIdentifier in all
    sessions


details: >
    Verify response for dynamicallyDefineDataIdentifier(0x2C) in default & extended session with
    response code 0x6C and it should not support in programming session.

    Also the maximum response time for the service dynamicallyDefineDataIdentifier(0x2C) should
    be less than 200ms.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.conf import Conf
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_file_io import SupportFileIO

CNF = Conf()
SC_CARCOM = SupportCARCOM()
SE27 = SupportService27()
SIO = SupportFileIO


def compare_positive_response(response, time_elapsed, parameters, session):
    """
    Compare dynamicallyDefineDataIdentifier(0x2C) positive response
    Args:
        response (str): ECU response code
        time_elapsed (int): response time
        parameters (dict): maximum response time and define did
        session (str): diagnostic session
    Returns:
        (bool): True on Success
    """
    result = False
    if response[2:4] == '6C' and response[4:8] == parameters['define_did']:
        if time_elapsed <= parameters['max_response_time']:
            logging.info("Received %s within %sms for request "
                         "dynamicallyDefineDataIdentifier(0x2C) in %s session as expected",
                          parameters['define_did'], parameters['max_response_time'], session)
            result = True
        else:
            logging.error("Test failed: Time elapsed %sms is greater than %sms in %s session",
                        time_elapsed, parameters['max_response_time'], session)
            result = False
    else:
        logging.error("Test failed: Expected positive response %s, received %s in %s session",
                        parameters['define_did'], response, session)
        result = False

    return result


def compare_negative_response(response, session, nrc_code):
    """
    Compare dynamicallyDefineDataIdentifier(0x2C) negative response
    Args:
        response (str): ECU response code
        session (str): diagnostic session
        nrc_code(str): negative response code
    Returns:
        (bool): True on Success
    """
    result = False
    if response[2:4] == '7F' and response[6:8] == nrc_code:
        logging.info("Received NRC %s for request dynamicallyDefineDataIdentifier(0x2C) in %s"
                        " session as expected", response, session)
        result = True
    else:
        logging.error("Test failed: Expected NRC %s for request"
                        " dynamicallyDefineDataIdentifier(0x2C) in %s session, received %s",
                        nrc_code, response, session)
        result = False
    return result


def request_dynamically_define_data_identifier(dut, parameters):
    """
    Initiate dynamicallyDefineDataIdentifier(0x2C)-defineByIdentifier request
    Args:
        dut (class object): dut instance
        define_did (str): dynamically define data identifier
    Returns:
        response: ECU response code
    """
    # payload = '2A sub-function= 01 define_did=F224 source_data_identifier=1A3B
    # position_in_source_data_record=03 memory_size=05'
    payload = SC_CARCOM.can_m_send("DynamicallyDefineDataIdentifier", b'\x01'
                                   + bytes.fromhex(parameters['define_did'])
                                   + bytes.fromhex(parameters['source_data_identifier'])
                                   + bytes.fromhex(parameters['position_in_source_data_record'])
                                   + bytes.fromhex(parameters['memory_size'])
                                   , b'')
    response = dut.uds.generic_ecu_call(payload)
    return response.raw


def step_1(dut: Dut):
    """
    action: Verify dynamicallyDefineDataIdentifier(0x2C)-defineByIdentifier request in default mode

    expected_result: ECU should send positive response within 200ms
    """
    # Read maximum response time and define did from yml file
    parameters_dict = { 'max_response_time': 0,
                        'define_did': '',
                        'source_data_identifier':'',
                        'position_in_source_data_record':'',
                        'memory_size':''
                    }
    parameters = SIO.parameter_adopt_teststep(parameters_dict)

    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False, None

    # Initiate DynamicallyDefineDataIdentifier
    response = request_dynamically_define_data_identifier(dut, parameters)
    time_elapsed = dut.uds.milliseconds_since_request()
    result = compare_positive_response(response, time_elapsed, parameters, 'default')

    return result, parameters


def step_2(dut: Dut, parameters):
    """
    action: Verify dynamicallyDefineDataIdentifier(0x2C)-defineByIdentifier request in programming
            mode
    expected_result: ECU should not support dynamicallyDefineDataIdentifier(0x2C)
                     in programming session
    """
    # Change to programming session
    dut.uds.set_mode(2)

    # Initiate DynamicallyDefineDataIdentifier
    response = request_dynamically_define_data_identifier(dut, parameters)
    result = compare_negative_response(response, session="programming", nrc_code='11')

    return result


def step_3(dut: Dut, parameters):
    """
    action: Verify dynamicallyDefineDataIdentifier(0x2C)-defineByIdentifier request in extended
            mode

    expected_result: ECU should send positive response within 200ms after security access
    """
    # Change to extended session
    dut.uds.set_mode(1)
    dut.uds.set_mode(3)

    # initiate DynamicallyDefineDataIdentifier without security access
    response = request_dynamically_define_data_identifier(dut, parameters)
    result_without_security = compare_negative_response(response, session="extended", nrc_code='33')

    # Security access to ECU
    security_access = SE27.activate_security_access_fixedkey(dut, CNF.default_rig_config,
                                                            step_no=272, purpose="SecurityAccess")
    if not security_access:
        logging.error("Test failed: security access denied in extended session")
        return False

    # initiate DynamicallyDefineDataIdentifier with security access
    response = request_dynamically_define_data_identifier(dut, parameters)
    time_elapsed = dut.uds.milliseconds_since_request()
    result_with_security = compare_positive_response(response, time_elapsed, parameters, 'extended')

    return result_without_security and result_with_security


# add for multiple sids in request

def run():
    """
    Verify the possibility to read out data with periodic transmission from ECUs within 200ms
    and also check service dynamicallyDefineDataIdentifier(0x2C)-defineByIdentifier request is
    protected by using the securityAccess
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=60)

        result_step, parameters = dut.step(step_1, purpose='Verify dynamicallyDefineDataIdentifier'
                                  '(0x2C)-defineByIdentifier response in default session')

        if result_step:
            result_step = dut.step(step_2, parameters['define_did'], purpose='Verify dynamicallyDefineDataIdentifier'
                                  '(0x2C)-defineByIdentifier response in programming session')

        if result_step:
            result_step = dut.step(step_3, parameters, purpose='Verify dynamicallyDefineDataIdentifier'
                                  '(0x2C)-defineByIdentifier response in extended session')
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
