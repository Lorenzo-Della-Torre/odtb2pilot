"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76173
version: 0
title: ReadMemoryByAddress (23) - addressAndLengthFormatIdentifier (ALFID)
purpose: >
	To make it easier for VOLVO CAR CORPORATION tools, the ECU shall support standardized request

description: >
    The ECU shall support the service readMemoryByAddress with the data parameter
    addressAndLengthFormatIdentifier set to one of the following values:
    •	0x14
    •	0x24

    The ECU shall support the data parameter in all sessions where the ECU supports the service
    readMemoryByAddress

details: >
    Verify readMemoryByAddress(0x23) with ALFIDs(0x14, 0x24) is supported in default and
    extended session and not in programming session.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_carcom import SupportCARCOM

SIO = SupportFileIO()
SC_CARCOM = SupportCARCOM()


def request_read_memory_by_address(dut, alfid, message):
    """
    Request readMemoryByAddress with ALFIDs 0x14,0x24
    Args:
        dut (Dut): An instance of Dut
        alfid (str): 0x14, 0x24
        message (str): Message
    Return:
        response.raw (str): ECU response
    """
    payload = SC_CARCOM.can_m_send("ReadMemoryByAddress", bytes.fromhex(message),
                                    bytes.fromhex(alfid))
    response = dut.uds.generic_ecu_call(payload)
    return response.raw


def verify_active_diagnostic_session(dut, ecu_session):
    """
    Request to check active diagnostic session
    Args:
        dut (Dut): An instance of Dut
        ecu_session (int): Diagnostic session
    Return:
        (bool): True when ECU is in expected session
    """
    result = dut.uds.active_diag_session_f186()

    if result.data["details"]["mode"] == ecu_session :
        logging.info("ECU is in mode %s as expected", ecu_session)
        return True

    logging.error("Test Failed: Expected session %s, received session %s",
                  ecu_session, result.data["details"]["mode"])
    return False


def verify_service_23_and_alfid(dut, alfid, message, session):
    """
    Verify readMemoryByAddress(0x23) with ALFID 0x14 and ALFID 0x24
    Args:
        dut (Dut): An instance of Dut
        alfid (str): 0x14, 0x24
        message (str): Message
        session (str): Diagnostic session
    Return:
        (bool): True when received positive response '63' for default and extended session
                and negative response '7F' and NRC-11(serviceNotSupported) for programming session
    """
    response = request_read_memory_by_address(dut, alfid, message)

    if session == 'programming':
        if response[2:4] == '7F' and response[6:8] == '11':
            logging.info("Successfully verified readMemoryByAddress is not supported for ALFID"
                         " 0x%s in %s session as expected", alfid, session)
            return True

        logging.error("Test Failed: Expected negative response '7F' and "
                      "NRC-11(serviceNotSupported) in %s session, received %s", session, response)
        return False

    if response[4:6] == '63':
        logging.info("Successfully verified readMemoryByAddress for ALFID 0x%s in %s session",
                      alfid, session)
        return True

    logging.error("Test Failed: Expected positive response '63' in %s session, received %s",
                  session, response)
    return False


def step_1(dut: Dut, parameters):
    """
    action: Verify readMemoryByAddress(0x23) with ALFID 0x14 and ALFID 0x24 in default session
    expected_result: True when received positive response '63'
    """
    result = verify_service_23_and_alfid(dut, parameters['alfid_14'],
             parameters['message_14'], session='default')
    if not result:
        return False

    result = verify_service_23_and_alfid(dut, parameters['alfid_24'],
             parameters['message_24'], session='default')
    if not result:
        return False

    return True


def step_2(dut: Dut, parameters):
    """
    action: Verify readMemoryByAddress(0x23) with ALFID 0x14 and ALFID 0x24 in extended session
    expected_result: True on receiving positive response '63'
    """
    # Set to extended session
    dut.uds.set_mode(3)

    result = verify_active_diagnostic_session(dut, ecu_session=3)
    if not result:
        return False

    result = verify_service_23_and_alfid(dut, parameters['alfid_14'],
             parameters['message_14'], session='extended')
    if not result:
        return False

    result = verify_service_23_and_alfid(dut, parameters['alfid_24'],
             parameters['message_24'], session='extended')
    if not result:
        return False

    return True


def step_3(dut: Dut, parameters):
    """
    action: Verify readMemoryByAddress(0x23) with ALFID 0x14 and ALFID 0x24 in programming session
    expected_result: True when received negative response '7F' and NRC-11(serviceNotSupported)
    """
    # Set to programming session
    dut.uds.set_mode(2)

    result = verify_active_diagnostic_session(dut, ecu_session=2)
    if not result:
        return False

    result = verify_service_23_and_alfid(dut, parameters['alfid_14'],
             parameters['message_14'], session='programming')
    if not result:
        return False

    result = verify_service_23_and_alfid(dut, parameters['alfid_24'],
             parameters['message_24'], session='programming')
    if not result:
        return False

    return True


def run():
    """
    Verify readMemoryByAddress(0x23) with ALFID's(0x14, 0x24) is supported in default and
    extended session and not in programming session.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'message_14': '',
                       'message_24': '',
                       'alfid_14':'',
                       'alfid_24':''}
    try:
        dut.precondition(timeout=60)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters, purpose="Verify readMemoryByAddress(0x23)"
                                                            " with ALFID 0x14 and ALFID 0x24 in"
                                                            " default session")
        if result_step:
            result_step = dut.step(step_2, parameters, purpose="Verify readMemoryByAddress(0x23)"
                                                               " with ALFID 0x14 and ALFID 0x24 in"
                                                               " extended session")
        if result_step:
            result_step = dut.step(step_3, parameters, purpose="Verify readMemoryByAddress(0x23)"
                                                                " with ALFID 0x14 and ALFID 0x24"
                                                                " in programming session")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
