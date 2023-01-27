"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 52291
version: 1
title: Enter bootloader from ECU application
purpose: >
    To define how to set the ECU to program mode when the ECU application is active.

description: >
    When all criteria for entering the bootloader has been met, it must be possible to enter the
    bootloader from the application by receiving the DiagnosticSessionControl(programmingSession)
    service only once.

details: >
    Verify ECU behaviour on receiving DiagnosticSessionControl request for different vehicle speed.
    Steps:
        1. ECU should be in programming session when vehicle velocity < 3km/h
        2. ECU should be in default session when vehicle velocity > 3km/h
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN, PerParam
from supportfunctions.support_file_io import SupportFileIO

SC = SupportCAN()
SIO = SupportFileIO()


def send_velocity_signal(dut, parameters, frame):
    """
    Send signal vehicle velocity
    Args:
        dut (Dut): An instance of Dut
        frame (str): Diagnostic session control frame
    Returns: None
    """
    can_p_ex: PerParam = {"name" : parameters['name'],
                          "send" : parameters['send'],
                          "id" : parameters['id'],
                          "frame" : frame,
                          "nspace" : dut[parameters['nspace']],
                          "intervall" : parameters['intervall']}

    SC.start_periodic(dut["netstub"], can_p_ex)


def verify_active_diagnostic_session(dut, mode, session):
    """
    Verify active diagnostic session
    Args:
        dut (Dut): An instance of Dut
        mode (int): ECU mode
        session (str): Diagnostic session
    Returns:
        (bool): True on successfully verifying active diagnostic session
    """
    response = dut.uds.active_diag_session_f186()
    if response.data["details"]["mode"] == mode:
        logging.info("ECU is in %s session as expected", session)
        return True

    logging.error("Test Failed: ECU is not in %s session", session)
    return False


def step_1(dut: Dut, parameters):
    """
    action: Verify ECU should be in programming session after session change request to programming
            when signal vehicle velocity < 3km/h
    expected_result: ECU should be in programming session
    """
    # Send signal vehicle velocity < 3km/h
    send_velocity_signal(dut, parameters, frame=bytes.fromhex(parameters['velocity_1']))

    # Change to programming session
    dut.uds.set_mode(2)
    result = verify_active_diagnostic_session(dut, mode=2, session='programming')

    # Stop periodic
    SC.stop_periodic("TesterPresent_periodic")

    return result


def step_2(dut: Dut, parameters):
    """
    action: Verify ECU should be in default session after session change request to programming
            when signal vehicle velocity > 3km/h
    expected_result: ECU should be in default session
    """
    # Change to default session
    dut.uds.set_mode(1)

    result = verify_active_diagnostic_session(dut, mode=1, session='default')
    if not result:
        return False

    # Send signal vehicle velocity > 3km/h
    send_velocity_signal(dut, parameters, frame=bytes.fromhex(parameters['velocity_2']))

    # Request session change to programming while car is moving, ECU should remain in default
    # session
    dut.uds.set_mode(2)
    result = verify_active_diagnostic_session(dut, mode=1, session='default')

    # Stop periodic
    SC.stop_periodic("TesterPresent_periodic")

    return result


def run():
    """
    Verify ECU behaviour on receiving the DiagnosticSessionControl request for different
    vehicle speed
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'name': '',
                       'send': bool,
                       'id': '',
                       'velocity_1': '',
                       'velocity_2': '',
                       'nspace': '',
                       'intervall': 0.0}

    try:
        dut.precondition(timeout=90)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters, purpose='Verify ECU should be in programming '
                                       'session after session change request to programming when '
                                       'signal vehicle velocity < 3km/h')
        if result_step:
            result_step = dut.step(step_2, parameters, purpose='Verify ECU should be in default '
                                           'session after session change request to programming '
                                           'when signal vehicle velocity > 3km/h')
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
