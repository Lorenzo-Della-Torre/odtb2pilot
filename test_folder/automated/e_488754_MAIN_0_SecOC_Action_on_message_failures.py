"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/


reqprod: 488754
version: 0
title: SecOC - Action on message failures

purpose: >
    To define what action to take when messages are failed due to SecOC

description: >
    When ECU fails to receive signals due to SecOC verification failures, Application
    software shall define and handle failure actions. Few possible actions can be:
    1. Use fail safe data values/actions
    2. Disable functions
    3. Temporarily accept failed signal data under specified range and conditions
    4. Report failures to security log
    5. Take no action

    If the application using SecOC requires hard start-up timing, meaning that the function
    must be available prior to the time is synched or available, the ECU need to implement special
    handling during those conditions. Such handling shall be analyzed to ensure that no
    vulnerabilities are introduced, that results in bypassing SecOC protection mechanism.

    Also, application functions shall be designed fault tolerant for SecOC verification failures
    in some ECU operating conditions such as low voltage conditions, power fluctuations, harsh
    environments, communication link disabled (E.g. Busoff in CAN), too many invalid messages
    received (Spoofing or replay attacks) etc. to ensure system behavior is never compromised.

details: >
    Verifying SecOC Action on Message Failures(Take no action)

"""


import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_seco import SecOCmsgVerification

SIO = SupportFileIO()
SECOCVERIFY = SecOCmsgVerification()


def step_1(dut: Dut):
    """
    action: Verifying SecOC Action on Message Failures
    expected_result: True on successful Message Failures signal found
    """
    # pylint: disable=unused-argument
    # Define did from yml file
    parameters_dict = {'signals':''}
    parameters = SIO.parameter_adopt_teststep(parameters_dict)
    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False, None

    result = []
    for signal in parameters['signals'].items():
        response = SECOCVERIFY.failed_message_take_no_action(signal)
        if response == 'Take no action':
            result.append(True)
        else :
            result.append(False)

    if len(result) != 0 and all(result):
        logging.info('message failures -> Take no action for signals')
        return True

    logging.error('Test Failed: no support to message failures')
    return False


def run():
    """
    Verifying SecOC Action on Message Failures.
    """
    dut = Dut()
    start_time = dut.start()
    result = False

    try:
        dut.precondition(timeout=30)

        result = dut.step(step_1, purpose="Verifying SecOC Action on Message Failures")
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
