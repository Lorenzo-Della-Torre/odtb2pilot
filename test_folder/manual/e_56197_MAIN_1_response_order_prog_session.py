"""

/*********************************************************************************/



Copyright © 2023 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 56197
version: 1
title: : Order of responses in programming session
purpose: >
    The order the server responds to queued requests must be defined.

description: >
    In programming session, physical diagnostic requests addressed to a server shall
    be processed and responded to in the order they were received..

"""

import logging
import time
from pprint import pprint

from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_file_io import SupportFileIO

SE10 = SupportService10()
SE22 = SupportService22()
SIO = SupportFileIO()
SSBL = SupportSBL()
SC = SupportCAN()



def step_1(dut: Dut):
    """
    action: Change to PROG.
    expected_result: ECU in PBL.
    """
    result = SE10.diagnostic_session_control_mode2(dut, stepno = 1)
    result = result and SE22.verify_pbl_session(dut)
    if not result:
        logging.error("Test Failed: Unable to switch to PBL")
    return result


def step_2(dut: Dut):
    """
    action: Send a number of DID requests, not waiting for reply
    expected_result:
    """
    result = True
    logging.info("Step2: clear can_frames")
    SC.clear_all_can_frames()
    logging.info("Step2: clear messages")
    SC.clear_all_can_messages()
    logging.info("Step2: messages cleared")

    #for cpay in (b'\xED\xA0', b'\xF1\xFB', b'\xED\xA0', b'\xF1\xFA', b'\xED\xA0',\
    #             b'x\F1\x86', b'\xED\xA0', b'x\F1\x2C', b'x\D0\xC7'):
    #    SC.t_send_signal_can_mf(dut, cpay)
    for payload in ('22EDA0', '22F1FB', '22EDA0', '22F1FA', '22EDA0', '22F186',\
                    '22EDA0', '22F12C', '22D0C7'):
        cpay = {'payload' : bytes.fromhex(payload), 'etp' : b''}
        logging.info("Step2 send cpay %s", cpay)
        SC.t_send_signal_can_mf(dut, cpay, padding=True, padding_byte=0x00)
    logging.info("Step2 wait 2sec for all DID to reply")
    return result


def step_3(dut: Dut):
    """
    action: Check if reply came in same order.
    expected_result: ECU should send positive response '62'.
    """

    result = True
    time.sleep(2)
    logging.info("Step_3, show frames in receive buffer")
    logging.info("Step3 Rec can sent frames: %s\n\n", pprint(SC.can_frames[dut["send"]]))
    logging.info("Step3 Rec can receive frames: %s\n\n", pprint(SC.can_frames[dut["receive"]]))
    SC.update_can_messages(dut)
    logging.info("Step3 Rec can receive messages: %s\n\n", SC.can_messages[dut["receive"]])
    frame_list = SC.can_frames[dut["receive"]]
    logging.info("Current list of received frames: %s\n\n", pprint(frame_list))

    return result


def step_4(dut):
    """
    action: Check if ECU still in PBL
    expected_result: ECU still in PBL
    """
    result = SE22.verify_pbl_session(dut)
    if not result:
        logging.error("Test Failed: ECU no longer in PBL")
    return result



def run():
    """
    Verify service 0x22(ReadDataByIdentifier) is supported in default, extended and programming
    session(PBL, SBL).
    """
    dut = Dut()

    start_time = dut.start()

    try:
        dut.precondition(timeout=240)

        result = dut.step(step_1,
                               purpose="Switch ECU to prog session (PBL)")
        result = result and dut.step(step_2, purpose="Send number of requests")
        result = result and dut.step(step_3, purpose="show/analyse received frames")
        result = result and dut.step(step_4, purpose="Verify ECU session PBL")

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
