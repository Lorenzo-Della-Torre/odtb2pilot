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
    Verify ECU is alive again within less than max-time(2500 ms) by requesting current ECU-mode
"""

import logging
import time
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_service22 import SupportService22

SIO = SupportFileIO()
SE22 = SupportService22()


def step_1(dut: Dut):
    """
    action: Request ECU reset
    expected_result: ECU restart done after 1 second
    """
    # Set ECU to Extended session
    dut.uds.set_mode(3)
    # ECU hard reset
    ecu_response = dut.uds.ecu_reset_1101()

    if ecu_response.raw[2:4] == '51':
        # Wait 1 second
        time.sleep(1)
        # Get current ECU mode
        ecu_mode = SE22.get_ecu_mode(dut)
        if ecu_mode == 'DEF':
            logging.info("ECU restarted after 1 second")
            logging.info("Received default mode %s as expected", ecu_mode)
            return True

        logging.error("ECU not restarted after 1 second")
        logging.error("Test failed: Expected default mode, received %s", ecu_mode)
        return False

    logging.error("Test failed: ECU reset not successful, expected '51', received %s",
                   ecu_response.raw)
    return False


def run():
    """
    Verify ECU is alive again within less than max-time(2500 ms) by requesting current ECU-mode
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    try:
        dut.precondition(timeout=30)

        result = dut.step(step_1, purpose="Verify ECU is alive again within less than 2500 ms"
                          " by requesting current ECU-mode")

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
