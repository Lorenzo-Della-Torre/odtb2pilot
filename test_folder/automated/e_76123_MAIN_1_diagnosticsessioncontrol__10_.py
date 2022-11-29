"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76123
version: 2
title: : DiagnosticSessionControl (10)
purpose: >

description: >
    The ECU must support the service diagnosticSessionControl. The ECU shall implement the service
    accordingly:

    Supported session:
    The ECU shall support Service diagnosticSessionControl in:
    • defaultSession
    • extendedDiagnosticSession
    • programmingSession, both primary and secondary bootloader

    Response time:
    Maximum response time for the service diagnosticSessionControl (0x10) is P2Server_max.

    Effect on the ECU normal operation, programmingSession:
    Transition from and to programmingSession is allowed to affect the ECUs ability to execute
    tasks that are non-diagnostic. The service is only allowed to affect execution of the
    non-diagnostic tasks during the execution of the diagnostic service. After the diagnostic
    service is completed any effect on the non-diagnostic tasks is not allowed anymore
    (normal operational functionality resumes).

    Effect on the ECU normal operation, other sessions than programmingSession:
    All other transitions than from and to programmingSession (excluding programmingSession to
    programmingSession) shall not affect the ECUs ability to execute non-diagnostic tasks.

    Entry conditions, programmingSession:
    Entry conditions for service diagnosticSessionConrol (0x10), changing to programmingSession
    (0x02) (excluding programmingSession to programmingSession):
    The implementer shall implement the ECUs condition for entering programmingSession based on
    the allocated functionality. The condition shall ensure a defined and safe vehicle state when
    entering programmingSession and must at a minimum include vehicle speed < 3km/h and usage
    mode ≠ Driving (if not otherwise approved Volvo Car Corporation).
    In an impaired vehicle or in a stand-alone scenario if the vehicle signal(s) used in the
    evaluation of the condition e.g. speed and/or "main propulsion system not active" is
    unavailable shall the safety mechanism not prevent the ECU to change to programmingSession
    to allow SWDL.
    If the ECU implement safety requirements with an ASIL higher than QM it shall, in all
    situations when diagnostic services may violate any of those safety requirements, reject the
    critical diagnostic service requests. Note that if the ECU rejects such critical diagnostic
    service requests, this requires an approval by Volvo Car Corporation.

    Entry conditions, other sessions than programmingSession:
    The ECU shall not implement entry conditions for service diagnosticSessionConrol (0x10) in
    other session transitions than changing to programmingSession (0x02).

    Security access:
    The ECU shall not protect service diagnosticSessionControl by using the service securityAccess
    (0x27).

details:
    Verify ECU behaviour on receiving DiagnosticSessionControl request for different vehicle speed.
    - ECU should be in programming session when vehicle velocity < 3km/h
    - ECU should be in default session when vehicle velocity > 3km/h
    And also verify session change request to extended should be acknowledged within p2_server time
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN, PerParam
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_test_odtb2 import SupportTestODTB2

SC = SupportCAN()
SIO = SupportFileIO()
SC_CARCOM = SupportCARCOM()
SE22 = SupportService22()
SUTE = SupportTestODTB2()


def verify_active_diagnostic_session(dut, mode, session):
    """
    Verify active diagnostic session
    Args:
        dut (Dut): An instance of Dut
        mode (int): Diagnostic mode
        session (str): Diagnostic session
    Returns:
        (bool): True on successfully verifying active diagnostic session
    """
    active_session = dut.uds.active_diag_session_f186()
    # Verify active diagnostic session
    if active_session.data["details"]["mode"] == mode:
        logging.info("ECU is in %s session as expected", session)
        return True

    logging.error("Test Failed: ECU is not in %s session", session)
    return False


def step_1(dut: Dut, parameters):
    """
    action: Send signal vehicle velocity < 3km/h
    expected_result: Periodic signal should be started
    """
    # Send velocity signal
    can_p_ex: PerParam = {"name" : parameters['name'],
                          "send" : parameters['send'],
                          "id" : parameters['id'],
                          "frame" : bytes.fromhex(parameters['velocity_1']),
                          "nspace" : dut["namespace"],
                          "intervall" : 0.015}

    SC.start_periodic(dut["netstub"], can_p_ex)
    # Wait 2s after starting periodic signal
    time.sleep(2)
    return True


def step_2(dut: Dut):
    """
    action: Set to programming session and verify active diagnostic session
    expected_result: ECU should be in programming session
    """
    # Set to programming session
    dut.uds.set_mode(2)
    # Wait 3s after changing mode
    time.sleep(3)

    return verify_active_diagnostic_session(dut, mode=2, session='programming')


def step_3(dut: Dut):
    """
    action: Set to default session and verify active diagnostic session
    expected_result: ECU should be in default session
    """
    # Set to default session
    dut.uds.set_mode(1)
    # Wait 3s after changing mode
    time.sleep(3)

    return verify_active_diagnostic_session(dut, mode=1, session='default')


def step_4(dut: Dut, parameters):
    """
    action: Acknowledge session change request to extended within p2_server time
    expected_result: ECU should send positive response
    """
    result = False
    # Send session change request to extended
    dut.uds.set_mode(3)
    # Wait for 30ms after sending multiple can frames
    time.sleep(parameters['sleep_time'])
    SC.update_can_messages(dut)
    elapsed_time = dut.uds.milliseconds_since_request()

    time.sleep(1)
    can_reply = SC.can_frames[dut["receive"]]
    if elapsed_time < parameters['p2_server_time']:
        logging.info("Elapsed time: %sms is less than p2_server time: %sms", elapsed_time,
                      parameters['p2_server_time'])
        result = True

    result = result and SUTE.test_message(can_reply, "5003")
    if result:
        logging.info("DiagnosticSessionControl acknowledged within time limits")

    time.sleep(3)
    result = result and SE22.read_did_f186(dut, dsession=b'\x03')
    return result


def step_5(dut: Dut):
    """
    action: Set to default session and verify active diagnostic session
    expected_result: ECU should be in default session
    """
    # Set to default session
    dut.uds.set_mode(1)
    # Wait 3s after changing mode
    time.sleep(3)

    return verify_active_diagnostic_session(dut, mode=1, session='default')


def step_6(dut: Dut, parameters):
    """
    action: Send signal vehicle velocity > 3km/h
    expected_result: Periodic signal should be started
    """
    # Send velocity signal
    can_p_ex: PerParam = {"name" : parameters['name'],
                          "send" : parameters['send'],
                          "id" : parameters['id'],
                          "frame" : bytes.fromhex(parameters['velocity_2']),
                          "nspace" : dut["namespace"],
                          "intervall" : 0.015}

    SC.set_periodic(can_p_ex)

    # Wait 2s after updating parameter to periodic signal
    time.sleep(2)

    SC.stop_periodic(parameters['name'])
    return True


def step_7(dut: Dut):
    """
    action: Request session change to programming while car is moving
    expected result: ECU should remain in default session
    """
    # Set to programming session
    response = dut.uds.generic_ecu_call(bytes.fromhex('1002'))
    if not (response.raw[2:4] == '7F' and response.raw[6:8] == '22'):
        logging.error("Expecting NRC-22 (ConditionNotCorrect) when session change to programming "
                      "while car is moving but received %s", response.raw)
        return False

    logging.info("Session change to programming not allowed while car is moving, "
                 "received NRC-22 (ConditionNotCorrect) as expected")

    # Wait 3s after changing mode
    time.sleep(3)

    result = verify_active_diagnostic_session(dut, mode=1, session='default')

    return result


def run():
    """
    Verify ECU should remain in default session after getting session change request to programming
    while vehicle is moving
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'name': '',
                       'send': '',
                       'id': '',
                       'velocity_1': '',
                       'velocity_2': '',
                       'sleep_time': 0.0,
                       'p2_server_time': 0}

    try:
        dut.precondition(timeout=90)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters, purpose="Send signal vehicle velocity < 3km/h")

        if result_step:
            result_step = dut.step(step_2, purpose="Set to programming session and verify active "
                                                   "diagnostic session")
        if result_step:
            result_step = dut.step(step_3, purpose="Set to default session and verify active "
                                                   "diagnostic session")
        if result_step:
            result_step = dut.step(step_4, parameters, purpose="Acknowledge session change request"
                                                              " to extended within p2_server time")
        if result_step:
            result_step = dut.step(step_5, purpose="Set to default session and verify active "
                                                   "diagnostic session")
        if result_step:
            result_step = dut.step(step_6, parameters, purpose="Send signal vehicle "
                                                               "velocity > 3km/h")
        if result_step:
            result_step = dut.step(step_7, purpose="Request session change to programming while "
                                                   "car is moving")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
