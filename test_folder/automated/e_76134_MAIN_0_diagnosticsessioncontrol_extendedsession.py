"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/


reqprod: 76134
version: 1
title: : DiagnosticSessionControl (10) extendedDiagnosticSession (03, 83)

purpose: >
    ExtendedDiagnosticSession shall be supported since not all services used by the service tools
    can be performed from defaultSession.

description: >
    The ECU shall support the service diagnosticSessionControl - extendedSession in:
    •	defaultSession
    •	extendedDiagnosticSession
    The ECU may support diagnosticSessionControl - extendedSession in programmingSession.

details: >
    Verify the response of diagnosticSessionControl(10) - extended session(03, 83)
    in default, programming and extended diagnostic session
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.uds import UdsEmptyResponse
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_test_odtb2 import SupportTestODTB2

SC = SupportCAN()
SC_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()


def ext_session_without_reply(dut: Dut):
    """
    Send the payload with no reply in extended session
    Args:
        dut(Dut): Dut instance
    Returns:
        response (bool): True on receiving no response
    """
    payload = SC_CARCOM.can_m_send("DiagnosticSessionControl", b'\x83', b'')
    try:
        dut.uds.generic_ecu_call(payload)
    except UdsEmptyResponse:
        pass

    if not SC.can_messages[dut["receive"]]:
        logging.info("Empty response received from ECU as expected")
        return True

    logging.error("Test Failed: Expected empty response, received %s",
                  SC.can_messages[dut["receive"]])
    return False


def verify_active_session(dut, mode, session):
    """
    Verify active diagnostic session
    Args:
        dut(Dut): Dut instance
        mode(int): Integer value of diagnostic session
        session(str): Diagnostic session
    Returns:
        (bool): True on successfully verifying active diagnostic session
    """
    # Read active diagnostic session
    active_session = dut.uds.active_diag_session_f186()

    # Verify active diagnostic session
    if active_session.data["details"]["mode"] == mode:
        logging.info("ECU is in %s session as expected", session)
        return True

    logging.error("Test Failed: ECU is not in %s session", session)
    return False


def set_diagnostic_session(dut, mode):
    """
    Set active diagnostic session
    Args:
        dut(Dut): Dut instance
        mode(bytes): Diagnostic session
    Returns:
        response.raw(str): ECU response
    """
    response = dut.uds.generic_ecu_call(SC_CARCOM.can_m_send("DiagnosticSessionControl",
                                                              mode, b''))
    return response.raw


def step_1(dut: Dut):
    """
    action: Set to extended session with(0x03) and without reply(0x83) from default session
    expected_result: True when ECU is in extended session
    """
    # Set to extended session
    set_diagnostic_session(dut, mode=b'\x03')

    # Set to default session
    set_diagnostic_session(dut, mode=b'\x01')
    time.sleep(1)

    # Set to extended session without reply
    response = ext_session_without_reply(dut)
    if not response:
        return False

    return verify_active_session(dut, mode=3, session='extended')


def step_2(dut: Dut):
    """
    action: Set to extended session without reply(0x83) from extended session(0x03)
    expected_result: True when ECU is in extended session
    """
    # Set to extended session
    set_diagnostic_session(dut, mode=b'\x03')

    # Set to extended session without reply
    response = ext_session_without_reply(dut)
    if not response:
        return False

    return verify_active_session(dut, mode=3, session='extended')


def step_3(dut: Dut):
    """
    action: Set to extended session from programming session, verify NRC 12
           (subFunctionNotSupported)
    expected_result: True when NRC 12 received and ECU is in programming session
    """
    # Set to programming session
    set_diagnostic_session(dut, mode=b'\x02')

    # Set to programming session
    set_diagnostic_session(dut, mode=b'\x02')

    # Set to extended session
    set_diagnostic_session(dut, mode=b'\x03')
    result =  SUTE.test_message(SC.can_messages[dut["receive"]], teststring='7F1012')
    if result:
        logging.info("Received NRC %s for DiagnosticSessionControl request as expected",
                      SUTE.pp_decode_7f_response(SC.can_frames[dut["receive"]][0][2]))
        return True

    return verify_active_session(dut, mode=2, session='programming')


def step_4(dut: Dut):
    """
    action: Set ECU in extended session without reply(0x83) from programming and verify NRC 12
            (subFunctionNotSupported)
    expected_result: True when ECU sends NRC 12
    """
    # Change to extended session without reply
    set_diagnostic_session(dut, mode=b'\x83')

    result = SUTE.test_message(SC.can_messages[dut["receive"]], teststring='7F1012')
    if result:
        logging.info("Received NRC %s for DiagnosticSessionControl request as expected",
                      SUTE.pp_decode_7f_response(SC.can_frames[dut["receive"]][0][2]))
        return True

    logging.error("Test Failed: Expected NRC 12 for DiagnosticSessionControl request,"
                  "received %s", SUTE.pp_decode_7f_response(SC.can_frames[dut["receive"]][0][2]))
    return False


def run():
    """
    Verify response of diagnosticSessionControl(10) - extended session(03, 83)
    in default, programming and extended diagnostic session
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=60)

        result_step = dut.step(step_1, purpose="Set to extended session with(0x03) and without "
                                               "reply(0x83) from default session")
        if result_step:
            result_step = dut.step(step_2, purpose="Set to extended session without reply(0x83) "
                                                   "from extended session(0x03")
        if result_step:
            result_step = dut.step(step_3, purpose="Set to extended session from programming "
                                                   "session, verify NRC 12")
        if result_step:
            result_step = dut.step(step_4, purpose="Set ECU in extended session without reply "
                                                   "(0x83) from programming and verify NRC 12")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
