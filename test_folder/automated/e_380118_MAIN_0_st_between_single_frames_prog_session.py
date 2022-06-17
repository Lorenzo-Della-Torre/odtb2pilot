"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 389118
version: 0
title: : Separation time between single frames - programming session
purpose: >
    To ensure no messages are lost and good timing performance.

description: >
    In programming session the ECU shall handle receiving single frames (SF N_PDU) with
    as short time apart as the CAN protocol allows. This applies both when the single frames
    are from the same sender and from different senders.
    Note: the shortest separation time of CAN frames is the minimum Interframe Space.

details:
    Verify two single frame can be sent with zero short time in programming session
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN, CanPayload, CanTestExtra
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_service22 import SupportService22

SC = SupportCAN()
SIO = SupportFileIO()
SE22 = SupportService22()


def two_single_frame_sent_with_zero_st(dut):
    """
    Send two single frame with ST = 0
    Args:
        dut (Dut): An instance of Dut
    Returns:
        boolean: True when two single frame can be sent with ST = 0
    """
    result = True

    cpay_1: CanPayload = {"payload_1": b'\x03\x22\xF1\x8C\x00\x00\x00\x00',
                          "extra": ''}
    SIO.parameter_adopt_teststep(cpay_1)

    cpay_2: CanPayload = {"payload_2": b'\x03\x22\xF1\x2B\x00\x00\x00\x00',
                          "extra": ''}
    SIO.parameter_adopt_teststep(cpay_2)

    etp: CanTestExtra = {"step_no": 2,
                         "purpose" : "verify that two single frame can be sent with ST = 0"}

    SIO.parameter_adopt_teststep(etp)

    SC.clear_all_can_messages()
    SC.clear_all_can_frames()

    #send two SF request consecutively
    SC.t_send_signal_hex(dut["netstub"], dut["send"], dut["namespace"],
                         cpay_1["payload_1"])
    SC.t_send_signal_hex(dut["netstub"], dut["send"], dut["namespace"],
                         cpay_2["payload_2"])

    time.sleep(1)
    SC.update_can_messages(dut)
    logging.info("Time first request sent: %s \n", SC.can_frames[dut["send"]][0][0])
    logging.info("Time second request sent: %s \n", SC.can_frames[dut["send"]][1][0])
    logging.info("Time difference between two frame sent: %s \n",
                 SC.can_frames[dut["send"]][1][0] - SC.can_frames[dut["send"]][0][0])
    logging.info("frames received: %s \n", SC.can_frames[dut["receive"]])
    #expected content reply and frame number to compare with from a default requests
    first_reply_cont = 'F18C'
    frame_to_comp_first_rep = SC.can_frames[dut["receive"]][0][2]
    second_reply_cont = 'F12B'
    frame_to_comp_second_rep = SC.can_frames[dut["receive"]][1][2]

    logging.info("Step%s: first_reply_cont before YML: %s", etp["step_no"], first_reply_cont)
    logging.info("Step%s: frame_to_comp_first_rep before YML: %s", etp["step_no"],
                 frame_to_comp_first_rep)
    logging.info("Step%s: second_reply_cont before YML: %s", etp["step_no"], second_reply_cont)
    logging.info("Step%s: frame_to_comp_second_rep before YML: %s", etp["step_no"],
                 frame_to_comp_second_rep)

    # use YML to specifying the expected reply if a different request is sended
    first_reply_cont_new = SIO.parameter_adopt_teststep('first_reply_cont')
    frame_to_comp_first_rep_new = SIO.parameter_adopt_teststep('frame_to_comp_first_rep')

    second_reply_cont_new = SIO.parameter_adopt_teststep('second_reply_cont')
    frame_to_comp_second_rep_new = SIO.parameter_adopt_teststep('frame_to_comp_second_rep')

    # don't set empty value if no replacement was found for first reply:
    if first_reply_cont_new:
        first_reply_cont = first_reply_cont_new
        frame_to_comp_first_rep = frame_to_comp_first_rep_new
    else:
        logging.info("Step%s first_reply_cont_new is empty. Discard.", etp["step_no"])

    logging.info("Step%s: first_reply_cont after YML: %s", etp["step_no"], first_reply_cont)
    logging.info("Step%s: frame_to_comp_first_rep after YML: %s", etp["step_no"],
                 frame_to_comp_first_rep)

    # don't set empty value if no replacement was found for second reply:
    if second_reply_cont_new:
        second_reply_cont = second_reply_cont_new
        frame_to_comp_second_rep = frame_to_comp_second_rep_new
    else:
        logging.info("Step%s second_reply_cont_new is empty. Discard.", etp["step_no"])

    logging.info("Step%s: second_reply_cont after YML: %s", etp["step_no"], second_reply_cont)
    logging.info("Step%s: frame_to_comp_second_rep after YML: %s", etp["step_no"],
                 frame_to_comp_second_rep)

    result = result and first_reply_cont in frame_to_comp_first_rep
    result = result and second_reply_cont in frame_to_comp_second_rep
    logging.info("Step %s teststatus:%s \n", etp['step_no'], result)
    return result


def step_1(dut: Dut):
    """
    action: Verify two single frame can be sent with zero short time in programming session
    expected_result: True when two single frame can be sent with zero short time
    """
    # Set to programming session
    dut.uds.set_mode(2)

    result = two_single_frame_sent_with_zero_st(dut)
    if not result:
        return False

    check_prog_session = SE22.read_did_f186(dut, dsession=b'\x02')
    if not check_prog_session:
        logging.error("ECU not in programming session")
        return False

    logging.info("ECU is in programming session")
    return True


def run():
    """
    Verify two single frame can be sent with zero short time
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    try:
        dut.precondition(timeout=60)

        result = dut.step(step_1, purpose="Verify two single frame can be sent with"
                                          " zero short time in programming session")

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
