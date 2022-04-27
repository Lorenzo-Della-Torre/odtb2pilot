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
    Verify response for dynamicallyDefineDataIdentifier(0x2C) - defineByIdentifier(01, 81) in all
    sessions and in default & extended session with response code 0x6C and it should not support in
    programming session.
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


def compare_positive_response(response, parameters, session):
    """
    Compare dynamicallyDefineDataIdentifier(0x2C)- defineByIdentifier(01, 81) positive response
    Args:
        response (str): ECU response code
        parameters (dict): define did
        session (str): diagnostic session
    Returns:
        (bool): True on Success
    """
    result = False
    if response[2:4] == '6C' and response[4:8] == parameters['define_did']:
        logging.info("Received positve response for dynamicallyDefineDataIdentifier(0x2C) response "
                    "%s, received %s in %s session", parameters['define_did'], response, session)
        result = True

    else:
        logging.error("Test Failed: Expected positive response %s, received %s in %s session",
                        parameters['define_did'], response, session)
        result = False

    return result


def compare_negative_response(response, session, nrc_code):
    """
    Compare dynamicallyDefineDataIdentifier(0x2C)- defineByIdentifier(01, 81) negative response
    Args:
        response (str): ECU response code
        session (str): diagnostic session
        nrc_code(str): negative response code

    Returns:
        (bool): True on Success
    """
    result = False
    if response[2:4] == '7F' and response[6:8] == nrc_code:
        logging.info("Received NRC %s for request dynamicallyDefineDataIdentifier(0x2C)- "
                     "defineByIdentifier(01, 81) in %s session as expected", response, session)
        result = True

    else:
        logging.error("Test Failed: Expected NRC %s for request"
                      " dynamicallyDefineDataIdentifier(0x2C)-defineByIdentifier(01, 81) in"
                      " %s session, received %s",nrc_code, response, session)
        result = False

    return result


def dynamically_define_data_identifier(dut, parameters):
    """
    Initiate dynamicallyDefineDataIdentifier(0x2C)-defineByIdentifier(01, 81) request
    Args:
        dut (class object): dut instance
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
    action: Verify dynamicallyDefineDataIdentifier(0x2C)-defineByIdentifier(01, 81) request in
            default session
    expected_result: ECU should send positive response
    """

    # Initiate DynamicallyDefineDataIdentifier
    response = dynamically_define_data_identifier(dut, parameters)
    result = compare_positive_response(response, parameters, 'default')
    if not result:
        return False

    define_did = parameters['define_did']
    # Verify response of dynamically defined did
    response = dut.uds.read_data_by_id_22(bytes.fromhex(define_did))
    if response.raw[2:4] == '62':
        logging.info("Received positive response for dynamically define did %s", define_did)
        return True

    logging.error("Test failed: Unable to get response of dynamically define did %s", define_did)
    return False


def step_2(dut: Dut, parameters):
    """
    action: Verify dynamicallyDefineDataIdentifier(0x2C)-defineByIdentifier(01, 81) request in
            programming session
    expected_result: ECU should not support dynamicallyDefineDataIdentifier(0x2C)
                     in programming session
    """
    # Change to programming session
    dut.uds.set_mode(2)

    # Initiate DynamicallyDefineDataIdentifier
    response = dynamically_define_data_identifier(dut, parameters)
    result = compare_negative_response(response, session="programming", nrc_code='11')

    return result


def step_3(dut: Dut, parameters):
    """
    action: Verify dynamicallyDefineDataIdentifier(0x2C)-defineByIdentifier(01, 81) request in
             extended session
    expected_result: ECU should send positive response after security access
    """
    # Change to extended session
    dut.uds.set_mode(1)
    dut.uds.set_mode(3)

    # initiate DynamicallyDefineDataIdentifier without security access
    response = dynamically_define_data_identifier(dut, parameters)
    result_without_security = compare_negative_response(response, session="extended"
                                                        , nrc_code='33')

    if not result_without_security:
        return False

    # Security access to ECU
    security_access = SE27.activate_security_access_fixedkey(dut, CNF.default_rig_config,
                                                            step_no=272, purpose="SecurityAccess")
    if not security_access:
        logging.error("Test Failed: security access denied in extended session")
        return False

    # Initiate DynamicallyDefineDataIdentifier with security access
    response = dynamically_define_data_identifier(dut, parameters)
    result_with_security = compare_positive_response(response, parameters, 'extended')

    if not result_with_security:
        return False

    define_did = parameters['define_did']
    # Verify response of dynamically defined did
    response = dut.uds.read_data_by_id_22(define_did)
    if response.raw[2:4] == '62':
        logging.info("Received positive response for dynamically define did %s", define_did)
        return True

    logging.error("Test failed: Unable to get response of dynamically define did %s", define_did)
    return False


def run():
    """
    Verify Service dynamicallyDefineDataIdentifier(0x2C)-defineByIdentifier(01, 81) is support
    in all sessions.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = { 'define_did': '',
                    'source_data_identifier':'',
                    'position_in_source_data_record':'',
                    'memory_size':''}
    try:

        # Read parameters from yml file
        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        dut.precondition(timeout=60)

        result_step = dut.step(step_1, parameters, purpose='Verify dynamicallyDefineDataIdentifier'
                                  '(0x2C)-defineByIdentifier(01, 81) response in default session')

        if result_step:
            result_step = dut.step(step_2, parameters, purpose='Verify '
                                  'dynamicallyDefineDataIdentifier(0x2C)-defineByIdentifier'
                                  '(01, 81) response in programming session')

        if result_step:
            result_step = dut.step(step_3, parameters, purpose='Verify '
                                  'dynamicallyDefineDataIdentifier(0x2C)-defineByIdentifier'
                                  '(01, 81) response in extended session')
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
