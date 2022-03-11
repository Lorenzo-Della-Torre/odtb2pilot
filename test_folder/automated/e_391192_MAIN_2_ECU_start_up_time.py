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
    Verify CAN frame response within 2500ms for ECU hard reset
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_file_io import SupportFileIO

SC = SupportCAN()
SIO = SupportFileIO()


def step_1(dut):
    """
    action: ECU hard reset and check CAN frame response within 2500ms
    expected_result: Positive response
    """
    # Read yml parameters
    parameters_dict = {'wakeup_time': '',
                       'pbl_sw_did': ''}
    parameters = SIO.parameter_adopt_teststep(parameters_dict)

    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False

    # ECU hard reset
    ecu_response = dut.uds.ecu_reset_1101()
    start_time = SC.can_messages[dut["receive"]][0][0]

    if ecu_response.raw[2:4] == '51':
        # Read DID: pbl_software_part_num_f125
        did_response = dut.uds.read_data_by_id_22((bytes.fromhex(parameters['pbl_sw_did'])))

        if did_response.raw[4:6] == '62':
            end_time = SC.can_messages[dut["receive"]][0][0]

            time_elapsed = (end_time - start_time)
            # Elapsed time is less than 2500ms
            if time_elapsed <= float(parameters['wakeup_time']):
                return True

            logging.error("Test Failed: Elapsed time is greater than %sms",
                        parameters['wakeup_time'])
            return False

    msg = "Test Failed: Expected positive response 51, received {}".format(ecu_response.raw)
    logging.error(msg)
    return False


def run():
    """
    Verify sufficient response time on frame level within 2500ms after ECU reset
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=30)

        result_step = dut.step(step_1, purpose="ECU hard reset and check "
                               "CAN frame response within 2500ms")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
