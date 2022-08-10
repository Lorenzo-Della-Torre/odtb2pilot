"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76133
version: 1
title: DiagnosticSessionControl(10) programmingSession (02, 82)
purpose: >
    It shall be possible to re-program any ECU on the public network.

description: >
    The ECU shall support the service diagnosticSessionControl - programmingSession in:
    •   defaultSession
    •   extendedDiagnosticSession
    •   programmingSession, both primary and secondary bootloader.

details: >
    Verify the response of request programming session with and without reply after setting ECU
    to default, programming and extended diagnostic session.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.uds import UdsEmptyResponse
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_can import SupportCAN

SC_CARCOM = SupportCARCOM()
SE22 = SupportService22()
SC = SupportCAN()


def prog_session_with_no_reply(dut: Dut):
    """
    Send the payload with no reply in programming session
    Args:
        dut (Dut): Dut instance
    Return:
        response (bool): True on receiving no response
    """
    payload = SC_CARCOM.can_m_send("DiagnosticSessionControl", b'\x82', b'')
    try:
        dut.uds.generic_ecu_call(payload)
    except UdsEmptyResponse:
        pass

    if not SC.can_messages[dut["receive"]]:
        logging.info("Empty response received from ECU")
        return True

    logging.error("Test Failed: Expected empty response, received %s",
                  SC.can_messages[dut["receive"]])
    return False


def step_1(dut: Dut):
    """
    action: Set to default session and request programming session with no reply
    expected_result: True when ECU is in programming session
    """
    # Set to programming session
    dut.uds.set_mode(2)

    # Set to default session
    dut.uds.set_mode(1)

    # Set to programming session with no reply
    response = prog_session_with_no_reply(dut)
    if not response:
        return False

    # Verify current session
    result = SE22.read_did_f186(dut, dsession=b'\x02')
    if result:
        logging.info("ECU is in programming session as expected")
        return True

    logging.error("Test Failed: ECU is not in programming session")
    return False


def step_2(dut: Dut):
    """
    action: Set to extended session and request programming session with and without reply
    expected_result: True when ECU is in programming session
    """
    # Set to default session
    dut.uds.set_mode(1)

    # Set to extended session
    dut.uds.set_mode(3)

    # Set to programming session
    dut.uds.set_mode(2)

    # Set to default session
    dut.uds.set_mode(1)

    # Set to extended session
    dut.uds.set_mode(3)

    # Set to programming session with no reply
    response = prog_session_with_no_reply(dut)
    if not response:
        return False

    # Verify current ECU session
    result = SE22.read_did_f186(dut, dsession=b'\x02')
    if result:
        logging.info("ECU is in programming session as expected")
        return True

    logging.error("Test Failed: ECU is not in programming session")
    return False


def step_3(dut: Dut):
    """
    action: Set to programming session and request programming session with no reply
    expected_result: True when ECU is in programming session
    """
    # Set to programming session
    dut.uds.set_mode(2)

    # Set to programming session with no reply
    response = prog_session_with_no_reply(dut)
    if not response:
        return False

    # Verify current ECU session
    result = SE22.read_did_f186(dut, dsession=b'\x02')
    if result:
        logging.info("ECU is in programming session as expected")
        return True

    logging.error("Test Failed: ECU is not in programming session")
    return False


def run():
    """
    Verify the response of request programming session with and without reply after setting ECU
    to default, programming and extended diagnostic session
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=60)

        result_step = dut.step(step_1, purpose="Set to default session and request programming "
                                               "session with no reply")
        if result_step:
            result_step = dut.step(step_2, purpose="Set to extended session and request "
                                                   "programming session with and without reply")
        if result_step:
            result_step = dut.step(step_3, purpose="Set to programming session and request "
                                                   "programming session with no reply")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
