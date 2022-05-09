"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76482
version: 1
title: : DynamicallyDefineDataIdentifier (2C) - clearDynamicallyDefinedDataIdentifier (03, 83)
purpose: >
    Standardized clear procedure to have compliance with VOLVO CAR CORPORATION tools

description: >
    The ECU shall support the service dynamicallyDefineDataIdentifier -
    clearDynamicallyDefinedDataIdentifier in all sessions where the ECU supports the service
    dynamicallyDefineDataIdentifier.

details: >
    Verify response for dynamicallyDefineDataIdentifier(0x2C) -
    clearDynamicallyDefinedDataIdentifier (03, 83) in default & extended session with response code
    0x6C and it should not support in programming session.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_file_io import SupportFileIO

SC_CARCOM = SupportCARCOM()
SE27 = SupportService27()
SIO = SupportFileIO


def compare_positive_response(response, define_did, session):
    """
    Compare dynamicallyDefineDataIdentifier(0x2C) request positive response
    Args:
        response (str): ECU response code
        define_did (dict): dynamically define data identifier
        session (str): diagnostic session
    Returns:
        (bool): True on Successfully verifying positive response
    """
    result = False
    if response[2:4] == '6C' and response[6:10] == define_did:
        logging.info("Received %s for request dynamicallyDefineDataIdentifier(0x2C) "
                        " in %s session as expected", define_did, session)
        result = True
    else:
        logging.error("Test failed: Expected positive response %s, received %s in %s session",
                        define_did, response, session)
        result = False

    return result


def compare_negative_response(response, session, nrc_code):
    """
    Compare dynamicallyDefineDataIdentifier(0x2C) request negative response
    Args:
        response (str): ECU response code
        session (str): diagnostic session
        nrc_code(str): negative response code
    Returns:
        (bool): True on Successfully verifying positive response
    """
    result = False
    if response[2:4] == '7F' and response[6:8] == nrc_code:
        logging.info("Received NRC %s for request dynamicallyDefineDataIdentifier(0x2C) "
                     " in %s session as expected", response, session)
        result = True
    else:
        logging.error("Test failed: Expected NRC %s for request"
                      "dynamicallyDefineDataIdentifier(0x2C) in %s session, received %s",
                       nrc_code, session, response)

        result = False
    return result


def request_dynamically_define_data_identifier(dut, define_did, sub_function):
    """
    Initiate dynamicallyDefineDataIdentifier(0x2C) request
    Args:
        dut (class object): dut instance
        define_did (str): dynamically define data identifier
        sub_function (str): subfunction of dynamicallyDefineDataIdentifier
    Returns:
        response: ECU response code
    """
    payload = SC_CARCOM.can_m_send("DynamicallyDefineDataIdentifier", bytes.fromhex(sub_function)
                                   + bytes.fromhex(define_did)
                                   , b'')
    response = dut.uds.generic_ecu_call(payload)
    return response.raw


def step_1(dut: Dut, define_did):
    """
    action: Verify dynamicallyDefineDataIdentifier(0x2C) - clearDynamicallyDefinedDataIdentifier
           (03, 83) request in default session

    expected_result: ECU should send positive response
    """
    # Initiate DynamicallyDefineDataIdentifier- clearDynamicallyDefinedDataIdentifier
    response = request_dynamically_define_data_identifier(dut, define_did, sub_function='03')
    result = compare_positive_response(response, define_did, 'default')
    if not result:
        return False

    # Verify dynamically defined data records are cleaned
    response = dut.uds.read_data_by_id_22(bytes.fromhex(define_did))
    if response.raw[2:4] == '62':
        logging.info("Test failed: Expected to receive negative response for %s did after clear"
                     " of dynamicallyDefineDataIdentifier", define_did)
        return False

    return True


def step_2(dut: Dut, define_did):
    """
    action: Verify dynamicallyDefineDataIdentifier(0x2C) - clearDynamicallyDefinedDataIdentifier
            (03, 83) in programming session
    expected_result: ECU should not support dynamicallyDefineDataIdentifier(0x2C) -
                     clearDynamicallyDefinedDataIdentifier (03, 83) in programming session
    """
    # Change to programming session
    dut.uds.set_mode(2)

    # Initiate DynamicallyDefineDataIdentifier
    response = request_dynamically_define_data_identifier(dut, define_did, sub_function='03')
    result = compare_negative_response(response, session="programming", nrc_code='7F')

    return result


def step_3(dut: Dut, define_did):
    """
    action: Verify dynamicallyDefineDataIdentifier(0x2C) - clearDynamicallyDefinedDataIdentifier
           (03, 83) request in extended session
    expected_result: ECU should send positive response after security access
    """
    # Change to extended session
    dut.uds.set_mode(1)
    dut.uds.set_mode(3)

    # Initiate DynamicallyDefineDataIdentifier- clearDynamicallyDefinedDataIdentifier
    #  without security access
    response = request_dynamically_define_data_identifier(dut, define_did, sub_function='03')
    result_without_security = compare_negative_response(response, session="extended", nrc_code='33')
    if not result_without_security:
        return False

    # Security access to ECU
    security_access = SE27.activate_security_access_fixedkey(dut, dut.conf.default_rig_config,
                                                            step_no=272, purpose="SecurityAccess")
    if not security_access:
        logging.error("Test failed: security access denied in extended session")
        return False

    # Initiate DynamicallyDefineDataIdentifier- clearDynamicallyDefinedDataIdentifier
    #  with security access
    response = request_dynamically_define_data_identifier(dut, define_did, sub_function='03')
    result_with_security = compare_positive_response(response, define_did, 'extended')
    if not result_with_security:
        return False

    # Verify dynamically defined data records are cleaned
    response = dut.uds.read_data_by_id_22(bytes.fromhex(define_did))
    if response.raw[2:4] == '62':
        logging.info("Test failed: Expected to receive negative response for %s did after clear"
                     " of dynamicallyDefineDataIdentifier", define_did)
        return False

    return True


def run():
    """
    Verify Service dynamicallyDefineDataIdentifier(0x2C)- clearDynamicallyDefinedDataIdentifier
    (03, 83) is supporting all sessions.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False
    parameters_dict = { 'define_did': '' }

    try:
        dut.precondition(timeout=60)

        # Extract yml parameters
        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters['define_did'], purpose='Verify '
                                                  'dynamicallyDefineDataIdentifier(0x2C) -'
                                                  ' clearDynamicallyDefinedDataIdentifier (03, 83)'
                                                  ' response in default session')

        if result_step:
            result_step = dut.step(step_2, parameters['define_did'], purpose='Verify '
                                                   'dynamicallyDefineDataIdentifier(0x2C) - '
                                                   'clearDynamicallyDefinedDataIdentifier (03, 83)'
                                                   ' negative response in programming session')

        if result_step:
            result_step = dut.step(step_3, parameters['define_did'], purpose='Verify '
                                                  'dynamicallyDefineDataIdentifier(0x2C) -'
                                                  ' clearDynamicallyDefinedDataIdentifier (03, 83)'
                                                  ' response in extended session')
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
