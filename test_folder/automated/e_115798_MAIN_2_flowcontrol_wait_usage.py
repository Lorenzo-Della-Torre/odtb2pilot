"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 115798
version: 2
title: Flowcontrol Wait usage
purpose: >
    Use FC.Wait to halt message reception in appropriate situations.

description: >
    Non-gateway server:
    In programming session, the server may use FC.Wait if it receives a request when it is
    processing a previously received request. In all other situations in all sessions usage
    of FC.Wait is not allowed.

    Gateway ECU:
    The gateway ECU shall use FC.Wait if it receives a message when buffers are not available
    for receiving the complete message. This applies to server side and client side.

details: >
    Verify FC-WAIT (31) by looking for fc_wait.txt file in a defined file path
"""

import os
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO

SIO = SupportFileIO()


def step_1(dut: Dut, parameters):
    """
    action: Look for fc_wait.txt file in a defined file path
    expected_result: Should get pass if file not found in defined path
    """
    # pylint: disable=unused-argument
    current_directory = os.getcwd()
    file_path = current_directory + parameters['fc_wait_path']
    # Look for the fc_wait.txt file
    path_to_fc_wait = os.path.exists(file_path)

    if path_to_fc_wait:
        logging.error("Test Failed: Received FC-WAIT (31), text file found in path: %s", file_path)
        return False

    logging.info("FC-WAIT (31) not received, text file not found in path")
    return True


def run():
    """
    Verify FC-WAIT (31) by looking for fc_wait.txt file in a defined file path
    """
    dut = Dut()

    start_time = dut.start()
    result = False

    parameters_dict = {'fc_wait_path': ''}
    try:
        dut.precondition(timeout=30)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameter not found")

        result = dut.step(step_1, parameters, purpose="Look for fc_wait.txt file in a defined "
                                                      "file path")

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
