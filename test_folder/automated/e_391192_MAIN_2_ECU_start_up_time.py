"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 391192
version: 2
title: ECU start up time
purpose: >
    Define a time the ECU is allowed to be unavailable in regards of diagnostic communication
    when powering up and the time shall be short enough to not be a problem for manufacturing
    and aftersales.

description: >
    The ECU shall complete its start-up sequence within 2500 ms after an event that initiates
    a start-up sequence. However, minimum the following events shall initiate a startup sequence:

    1.	Power up (the power supply is connected to the ECU) or waking up from sleep
        (the ECU receives a request to wake up by the operation cycle master).
    2.	An ECU hard reset is triggered.

details: >
    Verify CAN frame response for the following scenerios-
        1. Verify ECU is in Default session after reset
        2. Verify positive response after ECU wakeup (2500ms)
"""

import logging
import time
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO

SIO = SupportFileIO()


def step_1(dut: Dut):
    """
    action: Verify ECU is in Default session after reset
    expected_result: True when ECU is in Default session
    """
    # Set ECU to Extended session
    dut.uds.set_mode(3)
    # ECU hard reset
    ecu_response = dut.uds.ecu_reset_1101()
    # Wait 1 second
    time.sleep(1)

    if ecu_response.raw[2:4] == '51':
        response = dut.uds.active_diag_session_f186()

        if response.details["mode"] == '1':
            logging.info("Received default mode %s as expected", response.details["mode"])
            return True

        logging.error("Test failed: Expected default mode (1), received %s",
                       response.details["mode"])
        return False

    logging.error("Test failed: ECU reset not successful expected '51', received NRC %s",
                   ecu_response.raw)
    return False


def step_2(dut: Dut):
    """
    action: Verify positive response after ECU wakeup (2500ms)
    expected_result: True when successfully verified positive response after ECU wakeup (2500ms)
    """
    # pylint: disable=unused-argument

    # Read yml parameters
    parameters_dict = {'wakeup_time': 0,
                       'app_sw_did': ''}
    parameters = SIO.parameter_adopt_teststep(parameters_dict)

    if not all(list(parameters.values())):
        logging.error("Test failed: yml parameter not found")
        return False

    time.sleep((parameters['wakeup_time'])/1000)

    response = dut.uds.read_data_by_id_22(bytes.fromhex(parameters['app_sw_did']))

    if response.raw[4:6] == '62':
        logging.info("Received positive response %s as expected",response.raw[4:6])
        return True

    logging.error("Test failed: Expected positive response '62', received NRC %s",
                   response.raw)
    return False


def run():
    """
    Verify CAN frame response for the following scenerios-
        1. Verify ECU is in Default session after reset
        2. Verify positive response after ECU wakeup (2500ms)
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=30)

        result_step = dut.step(step_1, purpose="Verify ECU is in Default session after reset")

        if result_step:
            result_step = dut.step(step_2, purpose="Verify positive response after ECU "
                                   "wakeup (2500ms)")

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
