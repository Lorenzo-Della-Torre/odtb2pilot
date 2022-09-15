"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 60129
version: 3
title: Length of Classic CAN frames
purpose: >
    Define the length of USDT frames on CAN classic

description: >
    The DLC (DataLengthCode) of USDT frames on Classic CAN format shall always be set to eight
    bytes.

details: >
    Verify DLC(DataLengthCode) of USDT frames on classic can format is always set eight bytes.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_file_io import SupportFileIO

SIO = SupportFileIO()
SC = SupportCAN()
SUTE = SupportTestODTB2()


def step_1(dut: Dut, parameters):
    """
    action: Verify that a single frame reply is filled up to 8 bytes with x00
    expected_result: True when single frame reply is filled up to 8 bytes with x00
    """
    did_response = dut.uds.read_data_by_id_22(bytes.fromhex(
                                              parameters['read_active_diagnostic_session_did']))

    if did_response.raw[2:4] == '62':
        logging.info("Received positive response %s for request ReadDataByIdentifier as expected",
                      did_response.raw[2:4])
        # Verify received message is filled with 0 up to 8 bytes
        return SUTE.test_message(SC.can_messages[dut["receive"]],
                                   teststring = parameters['res_padded_frame'])

    logging.error("Test Failed: Expected positive response 62 for request ReadDataByIdentifier,"
                  " received %s", did_response.raw)
    return False


def step_2(dut: Dut, parameters):
    """
    action: Verify that last frame of a MF reply of DID FD00 is filled up to 8 bytes with x00
    expected_result: True when last frame of a MF reply of DID FD00 is filled up to 8 bytes
                     with x00
    """
    did_response = dut.uds.read_data_by_id_22(bytes.fromhex(parameters['power_supplies_did']))
    if did_response.raw[4:6] == '62':
        logging.info("Received positive response %s for request ReadDataByIdentifier as expected",
                      did_response.raw[4:6])
        # The reply to FD00 request is 12 bytes so the last frame should be filled with 5 bytes of 0
        return SUTE.test_message([SC.can_frames[dut["receive"]]
                                            [len(SC.can_frames[dut["receive"]])-1]],
                                            teststring=parameters['last_frame_padding'])

    logging.error("Test Failed: Expected positive response 62 for request ReadDataByIdentifier,"
                  " received %s", did_response.raw)
    return False


def run():
    """
    Verify DLC(DataLengthCode) of USDT frames on classic can format is always eight bytes
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'res_padded_frame' : '',
                       'last_frame_padding' : '',
                       'read_active_diagnostic_session_did' : '',
                       'power_supplies_did' : ''}
    try:
        dut.precondition(timeout=30)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters, purpose="Verify that a single frame reply is"
                                                           " filled up to 8 bytes with x00")
        if result_step:
            result_step = dut.step(step_2, parameters, purpose="Verify that last frame of a MF"
                                                               " reply of DID FD00 is filled up"
                                                               " to 8 bytes with x00")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
