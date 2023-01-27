"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 60064
version: 4
title: N_Cs Performance requirement in non-programming session
purpose: >
    The time spent waiting shall be minimized and especially for N_Cs since N_Cs wait time is
    the factor that affects the transfer rates the most. If the send mechanism is performed in
    application schedule context (compared to sending on Tx interrupt), the ECU needs to poll
    the send function more often, and thus less time will be spent on the applications normal
    functionality.

description: >
    When in non-programming session, the ECU shall be able to send Consecutive Frames with N_Cs
    less than 20ms.
    Note:
    a. If other CAN frames with higher priority exist on CAN, then a FC N_PDU may be delayed due to
    CAN protocol arbitration. The requirement is applicable and verifiable only when no such frame
    exist.
    b. For a client side of a gateway sending parallel requests, the CAN frames will have different
    CAN identifiers and hence different priority, and actual N_Cs may be higher than the
    requirement, this is expected.
    c. For a server, if other servers are sending responses in parallel then a FC N_PDU may be
    delayed due to CAN protocol arbitration, this is expected.
    d. The Autosar CAN Transport Layer configuration parameter CanTpNcs is not configuring the N_Cs
    performance defined by ISO-15765 although it is stated to be a performance configuration
    parameter. Instead CanTpNcs is configuring an internal timeout of getting data to be placed in
    the next Consecutive Frame. I.e. if no data can be retrieved internally for sending in a new
    Consecutive Frame, the sender will abort the transmission after CanTpNcs elapsed.

details: >
    Verify ECU sends consecutive frames with N_Cs less than 20ms in default and extended session
"""

import logging
import time
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_test_odtb2 import SupportTestODTB2

SC = SupportCAN()
SC_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()


def request_did(dut):
    """
    Request EDA0 - Complete ECU part/serial number
    Args:
        dut (Dut): An instance of Dut
    Returns:
        (bool): True when received MF reply
    """
    # Request EDA0 - Complete ECU part/serial number
    response = dut.uds.read_data_by_id_22(bytes.fromhex('EDA0'))
    if response.raw[4:6] == '62':
        logging.info("Received positive response for a request ReadDataByIdentifier to get MF "
                     "reply as expected")
        return True

    logging.error("Test Failed: Expected positive response for a request ReadDataByIdentifier "
                  "to get MF reply but not received")
    return False


def verify_messages(dut):
    """
    Verify received messages
    Args:
        dut (Dut): An instance of Dut
    Returns:
        (bool): True when whole message is received
    """
    time.sleep(5)
    time_stamp = [0]
    frame_stamp =["Sent"]

    logging.info("Sent message: %s", dut["send"])
    logging.info("Received message: %s", dut["receive"])

    logging.info("Frames sent %s", len(SC.can_frames[dut["send"]]))
    logging.info("Frames received %s", len(SC.can_frames[dut["receive"]]))

    SC.clear_all_can_messages()
    SC.update_can_messages(dut)

    time_stamp[0] = SC.can_frames[dut["send"]][0][0]
    frame_stamp[0] = "Sent: " + SC.can_frames[dut["send"]][0][2]
    time_stamp.append(SC.can_frames[dut["receive"]][0][0])
    frame_stamp.append("Received:" + SC.can_frames[dut["receive"]][0][2])
    time_stamp.append(SC.can_frames[dut["send"]][1][0])
    frame_stamp.append("Sent: " + SC.can_frames[dut["send"]][1][2])

    for i in range(1,len(SC.can_frames[dut["receive"]])):
        time_stamp.append(SC.can_frames[dut["receive"]][i][0])
        frame_stamp.append("Received:" + SC.can_frames[dut["receive"]][i][2])

    # First frame the request
    logging.info("timeStamp: %s, timeDiff: %s ms, diffToPrev: %s ms, %s",
                 time_stamp[0],
                 round(1000 * (time_stamp[0] - time_stamp[0]), 3),
                 round(1000 * (time_stamp[0] - time_stamp[0]), 3),
                 frame_stamp[0])

    # Second frame the FC.CTS
    logging.info("timeStamp: %s, timeDiff: %s ms, diffToPrev: %s ms, %s",
                 time_stamp[1],
                 round(1000 * (time_stamp[1] - time_stamp[0]), 3),
                 round(1000 * (time_stamp[1] - time_stamp[0]), 3),
                 frame_stamp[1])
    result = True

    # The rest of frames, the Consecutive Frames
    for i in range(2,len(SC.can_frames[dut["receive"]])+len(SC.can_frames[dut["send"]])):
        logging.info("timeStamp: %s, timeDiff: %s ms, diffToPrev: %s ms, %s",
                     time_stamp[i],
                     round(1000 * (time_stamp[i] - time_stamp[0]), 3),
                     round(1000 * (time_stamp[i] - time_stamp[i-1]), 3),
                     frame_stamp[i])
        result = result and (round(1000 * (time_stamp[i] - time_stamp[i-1]), 3) < 20.001)
    logging.info("All diffPrev between FC and CF < 20 ms : %s", result)

    return result


def verify_active_diagnostic_session(dut, ecu_session):
    """
    Request to check active diagnostic session
    Args:
        dut (Dut): An instance of Dut
        ecu_session (int): Diagnostic session
    Return:
        (bool): True when ECU is in expected session
    """
    result = dut.uds.active_diag_session_f186()

    if result.data["details"]["mode"] == ecu_session :
        logging.info("ECU is in mode %s as expected", ecu_session)
        return True

    logging.error("Test Failed: Expected session %s, received session %s",
                  ecu_session, result.data["details"]["mode"])
    return False


def step_1(dut: Dut):
    """
    action: Verify ECU sends consecutive frames with N_Cs in default session
    expected_result: ECU should be in default session after difference between FC and CF is less
                     than 20 ms
    """
    result = request_did(dut)
    if not result:
        return False

    result = verify_messages(dut)
    if not result:
        return False

    result = verify_active_diagnostic_session(dut, ecu_session=1)
    if not result:
        return False

    return True


def step_2(dut: Dut):
    """
    action: Verify ECU sends consecutive frames with N_Cs in extended session
    expected_result: Difference between FC and CF should be less than 20 ms
    """
    # Set to extended session
    dut.uds.set_mode(3)

    result = verify_active_diagnostic_session(dut, ecu_session=3)
    if not result:
        return False

    result = request_did(dut)
    if not result:
        return False

    result = verify_messages(dut)
    if not result:
        return False
    return True


def run():
    """
    Verify ECU sends consecutive frames with N_Cs less than 20ms in default and extended session
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=40)

        result_step = dut.step(step_1, purpose='Verify ECU sends consecutive frames'
                                               ' with N_Cs in default session')
        if result_step:
            result_step = dut.step(step_2, purpose='Verify ECU sends consecutive'
                                                   ' frames with N_Cs in extended session')
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
