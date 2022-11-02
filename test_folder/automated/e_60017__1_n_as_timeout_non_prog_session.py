"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 60017
version: 1
title: N_As timeout in non-programming session
purpose: >
    From a system perspective it is important that both sender and receiver side times out
    roughly the same time. The timeout value shall be high enough to not be affected by
    situations like occasional high busloads and low enough to get a user friendly system
    if for example an ECU is not connected.

description: >
    N_As timeout value shall be 1000ms in non-programming session.

details: >
    Verify N_As timeout value is 1000ms in non-programming session
    Steps:
        1. Send multi frame request DIDs with FC delay < 1000ms and FC delay > 1000ms for
           default session
        2. Send multi frame request DIDs with FC delay < 1000ms and FC delay > 1000ms for
           extended session
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.uds import UdsEmptyResponse
from supportfunctions.support_can import SupportCAN, CanMFParam

SC = SupportCAN()


def read_data_id_with_dids(dut):
    """
    Verify ReadDataByIdentifier service 22 with multiple DIDs
    Args:
        dut (Dut): An instance of Dut
    Returns:
        (bool): True on successfully verified non-empty response
    """
    # Send multi frame request DIDs with FC delay < 1000ms
    response = dut.uds.read_data_by_id_22(bytes.fromhex('DD02DD0ADD06F186'))
    if response is None:
        logging.error("Test Failed: Empty response")
        return False

    logging.info("Received a response for request ReadDataByIdentifier")
    return True


def change_control_frame_parameters(dut, frame_control_delay):
    """
    Request change frame control delay
    Args:
        dut (Dut): An instance of Dut
        frame_control_delay (int): Frame control delay
    Returns: None
    """
    can_mf: CanMFParam = {"block_size": 0,
                          "separation_time": 0,
                          "frame_control_delay": frame_control_delay,
                          "frame_control_flag": 48,
                          "frame_control_auto": True}

    SC.change_mf_fc(dut["receive"], can_mf)


def fc_less_than_1000_ms(dut):
    """
    Send multi frame request DIDs with FC delay < 1000ms
    Args:
        dut (Dut): An instance of Dut
    Returns:
        (bool): True when ECU supports multiple dataIdentifiers with FC delay < 1000ms
    """
    # Change control frame parameters
    change_control_frame_parameters(dut, frame_control_delay=950)

    # Send multi frame request DIDs with FC delay < 1000ms
    return read_data_id_with_dids(dut)


def fc_greater_than_1000_ms(dut):
    """
    Send multi frame request DIDs with FC delay > 1000ms
    Args:
        dut (Dut): An instance of Dut
    Returns:
        (bool): True when received empty response from ECU
    """
    # Change control frame parameters
    change_control_frame_parameters(dut, frame_control_delay=1050)

    # Send multi frame request DIDs with FC delay > 1000ms
    try:
        dut.uds.read_data_by_id_22(bytes.fromhex('DD02DD0ADD064947'))
    except UdsEmptyResponse:
        pass

    if not len(SC.can_messages[dut["receive"]]) == 0:
        logging.error("Test Failed: Expected 0 length of message, received: %s",
                      len(SC.can_messages[dut["receive"]]))
        return False

    # Set back frame_control_delay to default
    change_control_frame_parameters(dut, frame_control_delay=0)
    logging.info("Received message: %s as expected", SC.can_messages[dut["receive"]])
    return True


def step_1(dut: Dut):
    """
    action: Send multi frame request DIDs with FC delay < 1000ms and FC delay > 1000ms in
            default session
    expected_result: ECU should supports multiple dataIdentifiers with FC delay < 1000ms and
                     empty frame be received for FC delay > 1000ms in default session
    """
    result =  fc_less_than_1000_ms(dut)
    if not result:
        return False

    return fc_greater_than_1000_ms(dut)


def step_2(dut: Dut):
    """
    action: Send multi frame request DIDs with FC delay < 1000ms and FC delay > 1000ms in
            extended session
    expected_result: ECU should supports multiple dataIdentifiers with FC delay < 1000ms and
                     empty frame be received for FC delay > 1000ms in extended session
    """
    # Set ECU in extended session
    dut.uds.set_mode(3)

    # Check active diagnostic session
    response = dut.uds.active_diag_session_f186()
    if not response.data["details"]["mode"] == 3:
        logging.error('Test Failed: Not in extended session, received session %s',
                    response.data["details"]["mode"])
        return False

    result = fc_less_than_1000_ms(dut)
    if not result:
        return False

    return fc_greater_than_1000_ms(dut)


def run():
    """
    Verify N_As timeout value is 1000ms in non-programming session
    Steps:
        1. Send multi frame request DIDs with FC delay < 1000ms and FC delay > 1000ms for
           default session
        2. Send multi frame request DIDs with FC delay < 1000ms and FC delay > 1000ms for
           extended session
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=30)

        result_step = dut.step(step_1, purpose="Verify multi frame request DIDs with"
                               " FC delay < 1000ms and FC delay > 1000ms in default session")
        if result_step:
            result_step = dut.step(step_2, purpose="Verify multi frame request DIDs"
                                   " with FC delay < 1000ms and FC delay > 1000ms in extended"
                                   " session")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
