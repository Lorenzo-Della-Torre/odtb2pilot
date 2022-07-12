"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 60019
version: 1
title: N_Ar timeout in non-programming session
purpose: >
	From a system perspective it is important that both sender and receiver side times out roughly
    the same time. The timeout value shall be high enough to not be affected by situations like
    occasional high busloads and low enough to get a user friendly system if for example an ECU is
    not connected.

description: >
    N_Ar timeout value shall be 1000ms in non-programming session

details: >
    Verify FC delay for greater and lesser than timeout in non programming sessions
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN, CanMFParam, CanPayload, CanTestExtra
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM

SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()


def request_fc_delay_lesser_timeout(dut: Dut):
    """
    Send the payload requsting for FC delay lesser than timeout
    Args:
        dut (Dut): Dut instance
    Return:
        response (bool): True on receiving whole message
    """
    cpay: CanPayload = {"payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                        b'\xED\xA0',\
                                                        b''),
                        "extra": ''}

    etp: CanTestExtra = {"step_no" : 111,
                         "purpose" : '',
                         "timeout" : 2,
                         "min_no_messages" : -1,
                         "max_no_messages" : -1}

    # Change control frame parameters
    can_mf: CanMFParam = {"block_size": 0,
                          "separation_time": 0,
                          "frame_control_delay": 950,
                          "frame_control_flag": 48,
                          "frame_control_auto": True}

    SC.change_mf_fc(dut["receive"], can_mf)
    result = SUTE.teststep(dut, cpay, etp)
    logging.info("Messages received: %s", SC.can_messages[dut["receive"]])
    result = (len(SC.can_messages[dut["receive"]]) == 1)
    if result:
        logging.info("Received message as expected: %s", len(SC.can_messages[dut["receive"]]))
        return True

    logging.error("Test Failed: No request reply received, Received frames: %s",
                  len(SC.can_frames[dut["receive"]]))
    return False


def request_fc_delay_greater_timeout(dut):
    """
    Send the payload requsting for FC delay greater than timeout
    Args:
        dut (Dut): Dut instance
    Return:
        response (bool): True on receiving whole message
    """
    cpay: CanPayload = {"payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                        b'\xED\xA0',\
                                                        b''),
                        "extra": ''}

    etp: CanTestExtra = {"step_no" : 111,
                         "purpose" : '',
                         "timeout" : 5,
                         "min_no_messages" : -1,
                         "max_no_messages" : -1}

    # Change control frame parameters
    can_mf: CanMFParam = {"block_size": 0,
                          "separation_time": 0,
                          "frame_control_delay": 1100,
                          "frame_control_flag": 48,
                          "frame_control_auto": True}

    SC.change_mf_fc(dut["receive"], can_mf)
    result = SUTE.teststep(dut, cpay, etp)
    logging.info("Messages received: %s", SC.can_frames[dut["receive"]])
    result = (len(SC.can_frames[dut["receive"]]) == 1)
    if result:
        logging.info("Received message as expected: %s", len(SC.can_frames[dut["receive"]]))
        return True

    logging.error("Test Failed: No request reply received, Received frames: %s",
                  len(SC.can_frames[dut["receive"]]))
    return False


def set_back_fc_control_delay(dut):
    """
    Send the payload requsting for set back FC control delay
    Args:
        dut (class obj): Dut instance
    """
    # Change control frame parameters to default again
    can_mf: CanMFParam = {"block_size": 0,
                          "separation_time": 0,
                          "frame_control_delay": 0,
                          "frame_control_flag": 48,
                          "frame_control_auto": True}

    SC.change_mf_fc(dut["receive"], can_mf)


def step_1(dut: Dut):
    """
    action: Send request with FC_delay less than timeout in default session
    expected result: True on receiving whole message
    """
    result = request_fc_delay_lesser_timeout(dut)
    if result:
        # Send request for setting FC control delay
        set_back_fc_control_delay(dut)
        return True

    return False


def step_2(dut: Dut):
    """
    action: Send request with FC_delay greater than timeout in default session
    expected result: True on receiving whole message
    """
    result = request_fc_delay_greater_timeout(dut)
    if result:
        # Send request for setting FC control delay
        set_back_fc_control_delay(dut)
        return True

    return False


def step_3(dut: Dut):
    """
    action: Send request with FC_delay less than timeout in extended session
    expected result: whole message received
    """
    # Set to extended session
    dut.uds.set_mode(3)

    # Verify active diagnostic session
    response = dut.uds.active_diag_session_f186()
    if not response.data["details"]["mode"] == 3:
        logging.error("Test Failed: ECU is not in extended session")
        return False

    result = request_fc_delay_lesser_timeout(dut)
    if result:
        # Send request for setting FC control delay
        set_back_fc_control_delay(dut)
        return True

    return False


def step_4(dut: Dut):
    """
    action: Send request with FC_delay greater timeout in extended session
    expected result: whole message received
    """
    result = request_fc_delay_greater_timeout(dut)
    if result:
        # Send request for setting FC control delay
        set_back_fc_control_delay(dut)
        return True

    return False


def run():
    """
    Verify FC_delay for greater and lesser than timeout in both non programming sessions
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=60)

        result_step = dut.step(step_1, purpose="Send request with FC_delay less than timeout in "
                                               " default session")
        if result_step:
            result_step = dut.step(step_2, purpose="Send request with FC_delay greater than "
                                                   "timeout in default session")
        if result_step:
            result_step = dut.step(step_3, purpose="Send request with FC_delay less than timeout "
                                                   "in extended session")
        if result_step:
            result_step = dut.step(step_4, purpose="Send request with FC_delay greater timeout in "
                                                   "extended session")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
