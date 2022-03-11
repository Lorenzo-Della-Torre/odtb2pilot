"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 74107
version: 3
title: ECU ability to receive requests
purpose: >
    Define a time the ECU is allowed to be unavailable in regards of diagnostic communication
    when powering up and the time shall be short enough to not be a problem for manufacturing
    and aftersales.

description: >
    The ECU shall all the time be able to receive diagnostic service requests and send a response
    (positive or negative) on the requests as long as the ECU is within an operation cycle.

details: >
    Verify response for all sessions(Default, Extended and Programming) after ECU reset within
    operation cycle.
"""

import logging
import time
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN

SC = SupportCAN()


def step_1(dut):
    """
    action: ECU hard reset and check positive response within operation cycle
    expected_result: True when receive positive response and ECU is in DefaultSession
    """

    # ECU hard reset
    ecu_response = dut.uds.generic_ecu_call(bytes.fromhex('1101'))
    if not ecu_response.raw[2:4] == '51':
        logging.error("Test Failed: Invalid response, expected positive response 51, received %s",
                      ecu_response.raw[2:4])
        return False

    # Operation cycle delay 2500ms
    time.sleep(2.5)

    response = dut.uds.read_data_by_id_22(bytes.fromhex('F125'))
    active_session = dut.uds.active_diag_session_f186()

    if response.raw[4:6] == '62' and active_session.data["details"]["mode"] == 1:
        logging.info("The active DiagnosticSession is %s and response is %s as expected",
                     active_session.data["details"]["mode"], response.raw[4:6])
        return True

    logging.error("Test Failed: Expected ECU to be in default session and positive"
                  " response, received %s and %s", active_session.data["details"]["mode"],
                  response.raw[4:6])
    return False


def step_2(dut):
    """
    action: ECU hard reset and check positive response within operation cycle
    expected_result: True when receive positive response and ECU is in ExtendedSession
    """
    # ECU hard reset
    ecu_response = dut.uds.generic_ecu_call(bytes.fromhex('1101'))
    if not ecu_response.raw[2:4] == '51':
        logging.error("Test Failed: Invalid response, expected positive response 51, received %s",
                      ecu_response.raw[2:4])
        return False

    # Operation cycle delay 2500ms
    time.sleep(2.5)
    # Set extended DiagnosticSession
    dut.uds.set_mode(3)

    response = dut.uds.read_data_by_id_22(bytes.fromhex('F125'))
    active_session = dut.uds.active_diag_session_f186()

    if response.raw[4:6] == '62' and active_session.data["details"]["mode"] == 3:
        logging.info("The active DiagnosticSession is %s and response is %s as expected",
                     active_session.data["details"]["mode"], response.raw[4:6])
        return True

    logging.error("Test Failed: Expected ECU to be in extended session and positive"
                  " response, received %s and %s", active_session.data["details"]["mode"],
                  response.raw[4:6])
    return False


def step_3(dut):
    """
    action: ECU hard reset and check positive response within operation cycle
    expected_result: True when receive positive response and ECU is in ProgrammingSession
    """
    # ECU hard reset
    ecu_response = dut.uds.generic_ecu_call(bytes.fromhex('1101'))
    if not ecu_response.raw[2:4] == '51':
        logging.error("Test Failed: Invalid response, expected positive response 51, received %s",
                      ecu_response.raw[2:4])
        return False

    # Operation cycle delay 2500ms
    time.sleep(2.5)
    # Set programming DiagnosticSession
    dut.uds.set_mode(2)

    response = dut.uds.read_data_by_id_22(bytes.fromhex('F125'))
    active_session = dut.uds.active_diag_session_f186()

    if response.raw[4:6] == '62' and active_session.data["details"]["mode"] == 2:
        logging.info("The active DiagnosticSession is %s and response is %s as expected",
                    active_session.data["details"]["mode"], response.raw[4:6])
        return True

    logging.error("Test Failed: Expected ECU to be in programming session and positive"
                  " response, received %s and %s", active_session.data["details"]["mode"],
                  response.raw[4:6])
    return False

def run():
    """
    Check ECU is able to receive diagnostic service requests and verify response
    (positive or negative) on the requests within operation cycle (after 2500ms)
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=60)

        result_step = dut.step(step_1, purpose="ECU hard reset and check diagnostic service"
                                               " response for DefaultSession within an operation"
                                               " cycle")
        if result_step:
            result_step = dut.step(step_2, purpose="ECU hard reset and check diagnostic service"
                                                   " response for ExtendedSession within an"
                                                   " operation cycle")

        if result_step:
            result_step = dut.step(step_3, purpose="ECU hard reset and check diagnostic service"
                                                   " response for ProgrammingSession within an"
                                                   " operation cycle")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
