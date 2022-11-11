"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 74507
version: 2
title: Negative response code busyRepeatRequest (0x21)
purpose: >
    Standardise the negative response codes that an ECU may send to make it easier to understand
    why a ECU rejects a diagnostic service request.

description: >
    Rationale: The ECU shall always be ready to receive diagnostic request within its normal
    operation cycle. Negative response code busyRepeatRequest (0x21) will create disturbance in
    the manufacturing and aftersales process and is not generally allowed to be used by the ECU.

    Req: The negative response code busyRepeatRequest (0x21) sent by negative responses on
    diagnostic services requests is not allowed unless otherwise is specified by this document.

details: >
    Verify negative response code busyRepeatRequest(0x21).
"""

import os
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO

SIO = SupportFileIO()


def step_1(dut: Dut, paramters):
    """
    action: Verify negative response code busyRepeatRequest(0x21)
    expected_result: ECU should not send busyRepeatRequest(0x21) in response of diagnostic
                     request
    """
    # pylint: disable=unused-argument
    current_directory = os.getcwd()
    file_path = current_directory + paramters['nrc21_path']
    path_to_nrc_21 = os.path.exists(file_path)

    if not path_to_nrc_21:
        logging.error("Test Failed: File not found in path: %s", file_path)
        return False

    with open(file_path, 'r') as file:
        # Read all content from a file
        content = file.read()
        # Check if string present or not in file
        word = paramters['find_text']
        if word.lower() in content.lower():
            logging.error("Test Failed: Received NRC-21(busyRepeatRequest)")
            return False

        logging.info("NRC-21(busyRepeatRequest) not received from the ECU as expected "
                     "in the nightly run")
        return True


def run():
    """
    Verify negative response code busyRepeatRequest(0x21)
    """
    dut = Dut()

    start_time = dut.start()
    result = False

    parameters_dict = {'nrc21_path': '',
                       'find_text':''}

    try:
        dut.precondition(timeout=30)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameter not found")

        result = dut.step(step_1, parameters, purpose="Verify negative response code "
                                                      "busyRepeatRequest(0x21)")

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
