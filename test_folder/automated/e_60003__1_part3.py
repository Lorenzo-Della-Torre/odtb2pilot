"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 60003
version: 1
title: Transport and Network layer
purpose: >
    Standardise communication to ensure all ECUs uses the same diagnostic communication
    specifications. ISO standard shall be followed as far as possible unless otherwise specified
    to reduce cost and make implementation easier.

description: >
    The transport/network layer shall be compliant to Road vehicles - Diagnostic communication over
    Controller Area Network (DoCAN) - Part 2: Transport protocol and network layer services with the
    restrictions/additions as defined by this document. If there are contradictions between this
    specification, LC : VCC - DoCAN, and Road vehicles - Diagnostic communication over Controller
    Area Network (DoCAN) - Part 2: Transport protocol and network layer services, then this
    specification shall override Road vehicles - Diagnostic communication over Controller Area
    Network (DoCAN) - Part 2: Transport protocol and network layer services.

details: >
    Request ReadDataByIdentifier(0x22) with DID EDA0 to get MF reply and verify all the expected
    DIDs are present in received message
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_can import SupportCAN, CanTestExtra, CanPayload, CanMFParam
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_test_odtb2 import SupportTestODTB2

SIO = SupportFileIO()
SC = SupportCAN()
SC_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()


def verify_fc_wait_and_fc_cts(dut, fc_delay, fc_flag, max_delay=1):
    """
    Verify frame control with max number of WAIT frames and change frame control to continue
    to send (0x30)
    Args:
        dut (Dut): Dut instance
        fc_delay (int): Frame control delay
        fc_flag (str): Frame control flag
        max_delay (int): Maximum delay time
    Returns: None
    """
    can_mf: CanMFParam = {"block_size": 0,
                          "separation_time": 0,
                          "frame_control_delay": fc_delay,
                          "frame_control_flag": fc_flag,
                          "frame_control_auto": False}
    SC.change_mf_fc(dut["send"], can_mf)
    sig = dut["send"]

    for _ in range(max_delay):
        # frame_control_delay / 1000
        time.sleep(SC.can_subscribes[sig][3]/1000)

        SC.send_fc_frame(dut, frame_control_flag=SC.can_subscribes[sig][4],
                         block_size=SC.can_subscribes[sig][1],
                         separation_time=SC.can_subscribes[sig][2])

        logging.info("DelayNo.: %s, Number of can_frames received: %s",
                     SC.can_subscribes[sig][5], len(SC.can_frames[sig]))
        if max_delay > 1:
            # Frame control responses
            SC.can_subscribes[sig][5] += 1


def log_can_messages_frames_data():
    """
    Log data of CAN messages and CAN frames
    Args: None
    Returns: None
    """
    logging.info("Messages received %s", len(SC.can_messages))
    for message, data in SC.can_messages.items():
        logging.info("%s: %s", message, data)

    logging.info("Frames received %s", len(SC.can_frames))
    for frame_type, frames in SC.can_frames.items():
        logging.info("%s:", frame_type)

        for frame in frames:
            logging.info("%s", frame)


def step_1(dut: Dut):
    """
    action: Verify ECU's active diagnostic session
    expected_result: ECU should be in default session
    """
    # Verify active diagnostic session
    res = dut.uds.active_diag_session_f186()
    if res.data['details']['mode'] != 1:
        logging.error("Test Failed: ECU is not in default session")
        return False

    logging.info("ECU is in default session as expected")
    return True


def step_2(dut: Dut):
    """
    action: Request ReadDataByIdentifier(0x22) with DID EDA0 to get MF reply
    expected_result: ECU should give positive response '62'
    """
    cpay: CanPayload = {"payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                        bytes.fromhex('EDA0'),
                                                        b""),
                        "extra": b''}

    etp: CanTestExtra = {"step_no": 102,
                         "purpose": '',
                         "timeout": 0.0,
                         "min_no_messages": -1,
                         "max_no_messages": -1}

    can_mf: CanMFParam = {"block_size": 0,
                          "separation_time": 0,
                          "frame_control_delay": 970,
                          "frame_control_flag": 49,
                          "frame_control_auto": False}

    SC.change_mf_fc(dut["send"], can_mf)

    result = SUTE.teststep(dut, cpay, etp)
    if result:
        logging.info("Received positive response for a request ReadDataByIdentifier to get MF "
                     "reply as expected")
        return True

    logging.error("Test Failed: Expected positive response for a request ReadDataByIdentifier "
                  "to get MF reply but not received")
    return False


def step_3(dut: Dut, parameters):
    """
    action: Verify frame control with max number of WAIT frames
    expected_result: Successfully verified frame control with max number of WAIT frames
    """
    verify_fc_wait_and_fc_cts(dut, fc_delay=970, fc_flag=0x31,
                              max_delay=parameters['max_delay'])
    return True


def step_4(dut: Dut, parameters):
    """
    action: Verify DIDs in ECU response
    expected_result: All DIDs should be present in ECU response
    """
    # Change frame control to continue to send (0x30)
    verify_fc_wait_and_fc_cts(dut, fc_delay=0, fc_flag=0x30, max_delay=1)

    sig = dut["receive"]
    SC.clear_all_can_messages()
    SC.update_can_messages(dut)

    log_can_messages_frames_data()

    results=[]
    for teststring in parameters['teststrings']:
        result = SUTE.test_message(SC.can_messages[sig], teststring=teststring)
        if not result:
            logging.error("%s is not found in ECU response", teststring)
        results.append(result)

    if all(results) and len(results) != 0:
        logging.info("All DIDs are present in ECU response")
        return True

    logging.error("Test Failed: Some of the DIDs are not present in ECU response")
    return False


def run():
    """
    Request ReadDataByIdentifier(0x22) with DID EDA0 to get MF reply and verify all the expected
    DIDs are present in received message
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'max_delay': 0,
                       'teststrings': []}
    try:
        dut.precondition(timeout=300)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, purpose="Verify ECU's active diagnostic session")

        if result_step:
            result_step = dut.step(step_2, purpose="Request ReadDataByIdentifier(0x22) with DID "
                                                   "EDA0 to get MF reply")
        if result_step:
            result_step = dut.step(step_3, parameters, purpose="Verify frame control with max "
                                                               "number of WAIT frames")
        if result_step:
            result_step = dut.step(step_4, parameters, purpose="Verify DIDs in ECU response")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
