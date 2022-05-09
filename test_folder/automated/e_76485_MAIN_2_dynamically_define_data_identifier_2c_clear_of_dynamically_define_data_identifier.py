"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76485
version: 2
title: DynamicallyDefineDataIdentifier (2C)-clear of dynamicallyDefineDataIdentifier
purpose: >
    Clear of dynamicallyDefineDataIdentifier

description: >
    The dynamically defined data records that the ECU supports shall be kept until they are
    cleared by the service DynamicallyDefineDataIdentifier - clearDynamicallyDefinedDataIdentifier

details: >
    Verify response dynamically defined data records that the ECU supports shall be kept until
    they are cleared by the service DynamicallyDefineDataIdentifier -
    clearDynamicallyDefinedDataIdentifier
"""


import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_file_io import SupportFileIO

SC_CARCOM = SupportCARCOM()
SE22 = SupportService22()
SE27 = SupportService27()
SIO = SupportFileIO


def compare_positive_response(response, define_did, session):
    """
    Compare dynamicallyDefineDataIdentifier(0x2C) - clear of dynamicallyDefineDataIdentifier
    positive response

    Args:
        response (str): ECU response code
        define_did (str): dynamically define did
        session (str): diagnostic session
    Returns:
        (bool): True on successfully verified positive response
    """
    result = False
    if response[2:4] == '6C' and response[4:8] == define_did:
        logging.info("Received %s for request dynamicallyDefineDataIdentifier(0x2C) - "
                     " clear of dynamicallyDefineDataIdentifier in %s session as expected",
                     define_did, session)
        result = True

    else:
        logging.error("Test Failed: Expected positive response %s, received %s in %s session",
                        define_did, response, session)
        result = False

    return result


def compare_negative_response(response, session, nrc_code):
    """
    Compare dynamicallyDefineDataIdentifier(0x2C) - clear of dynamicallyDefineDataIdentifier
    negative response

    Args:
        response (str): ECU response code
        session (str): diagnostic session
        nrc_code (str): negative response code
    Returns:
        (bool): True on successfully verified negative response
    """
    result = False
    if response[2:4] == '7F' and response[6:8] == nrc_code:
        logging.info("Received NRC %s for request dynamicallyDefineDataIdentifier(0x2C) -"
                     "clear of dynamicallyDefineDataIdentifier  in %s session as expected ",
                     response, session)
        result = True

    else:
        logging.error("Test failed: Expected NRC %s for request "
                      "dynamicallyDefineDataIdentifier(0x2C) - clear of "
                      " dynamicallyDefineDataIdentifier in %s session, received %s",
                        nrc_code, response, session)
        result = False
    return result


def dynamically_define_data_identifier(dut, define_did, sub_function):
    """
    Initiate dynamicallyDefineDataIdentifier(0x2C) - clear of dynamicallyDefineDataIdentifier
    request
    Args:
        dut (Dut): dut instance
        define_did (str): dynamically defined did
        sub_function (str): subfunction of dynamicallyDefineDataIdentifier
    Returns:
        response (str): ECU response code
    """
    payload = SC_CARCOM.can_m_send("DynamicallyDefineDataIdentifier", bytes.fromhex(sub_function)
                                + bytes.fromhex(define_did)
                                , b'')
    response = dut.uds.generic_ecu_call(payload)
    return response.raw


def step_1(dut: Dut, define_did):
    """
    action: Verify defined data records are available until clear of
            dynamicallyDefineDataIdentifier request in default session
    expected_result: Dynamically defined data records are available until clear of
                     dynamicallyDefineDataIdentifier in default session
    """
    # Initiate DynamicallyDefineDataIdentifier
    response = dynamically_define_data_identifier(dut, define_did, sub_function='01')
    result = compare_positive_response(response, define_did, 'default')
    if not result:
        return False

    # Verify response of dynamically defined did
    response = dut.uds.read_data_by_id_22(bytes.fromhex(define_did))
    if response.raw[2:4] != '62':
        logging.error("Test failed: Unable to get response of dynamically define did %s",
					   define_did)
        return False

    # ECU reset
    dut.uds.ecu_reset_1101()
    # Verify ECU Reset is completed by checking active session is default
    is_in_default = SE22.read_did_f186(dut, b'\x01')
    if not is_in_default:
        logging.error("Test failed: Expected ECU to be in default session after ECU reset")
        return False

    # Verify response of dynamically defined did after ECU reset
    response = dut.uds.read_data_by_id_22(bytes.fromhex(define_did))
    if response.raw[2:4] != '62':
        logging.error("Test failed: Unable to get response of dynamically define did %s",
                       define_did)
        return False

    return True


def step_2(dut: Dut, define_did):
    """
    action: Verify dynamicallyDefineDataIdentifier(0x2C) - clear of dynamicallyDefineDataIdentifier
            in programming session
    expected_result: ECU should not support dynamicallyDefineDataIdentifier(0x2C) -
                     clear of dynamicallyDefineDataIdentifier in programming session
    """
    # Change to programming session
    dut.uds.set_mode(2)

    # Initiate DynamicallyDefineDataIdentifier - clear of dynamicallyDefineDataIdentifier
    response = dynamically_define_data_identifier(dut, define_did, sub_function='03')
    result = compare_negative_response(response, session="programming", nrc_code='7F')
    return result


def step_3(dut: Dut, define_did):
    """
    action: Verify defined data records are available until dynamicallyDefineDataIdentifier(0x2C) -
            clear of dynamicallyDefineDataIdentifier request in extended session
    expected_result: Dynamically defined data records are available until clear of
                     dynamicallyDefineDataIdentifier in extended session
    """
    # Change to extended session
    dut.uds.set_mode(1)
    dut.uds.set_mode(3)

    # Security access to ECU
    security_access = SE27.activate_security_access_fixedkey(dut, dut.conf.default_rig_config,
                                                            step_no=272, purpose="SecurityAccess")
    if not security_access:
        logging.error("Test failed: Security access denied in extended session")
        return False

    # Initiate DynamicallyDefineDataIdentifier
    response = dynamically_define_data_identifier(dut, define_did, sub_function='01')
    result = compare_positive_response(response, define_did, 'extended')
    if not result:
        return False

    # Verify response of dynamically defined did
    response = dut.uds.read_data_by_id_22(bytes.fromhex(define_did))
    if response.raw[2:4] != '62':
        logging.error("Test failed: Unable to get response of dynamically define did %s",
					   define_did)
        return False

    # ECU reset
    dut.uds.ecu_reset_1101()
    # Verify ECU reset is completed by checking active session is default
    is_in_default = SE22.read_did_f186(dut, b'\x01')
    if not is_in_default:
        logging.error("Test failed: Expected ECU to be in default session after ECU reset")
        return False

    # Verify response of dynamically defined did after ECU reset
    response = dut.uds.read_data_by_id_22(bytes.fromhex(define_did))
    if response.raw[2:4] != '62':
        logging.error("Test failed: Unable to get response of dynamically define did %s",
                       define_did)
        return False

    return True


def run():
    """
    Verify defined data records are available until clear of Service
    dynamicallyDefineDataIdentifier(0x2C)-clear of dynamicallyDefineDataIdentifier is supporting
    in default and extended session
    """

    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False
    parameters_dict = { 'define_did': ''}

    try:
        dut.precondition(timeout=60)
        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameter not found")

        result_step = dut.step(step_1, parameters['define_did'], purpose='Verify '
                                'dynamicallyDefineDataIdentifier(0x2C) - clear of '
                                'dynamicallyDefineDataIdentifier response in default session')


        if result_step:
            result_step = dut.step(step_2, parameters['define_did'], purpose='Verify'
                                    'dynamicallyDefineDataIdentifier(0x2C) -clear of '
                                    'dynamicallyDefineDataIdentifier negative response in '
                                    'programming session')

        if result_step:
            result_step = dut.step(step_3, parameters['define_did'], purpose='Verify '
                                    'dynamicallyDefineDataIdentifier(0x2C) -clear of '
                                    'dynamicallyDefineDataIdentifier response in '
                                    'extended session')
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
