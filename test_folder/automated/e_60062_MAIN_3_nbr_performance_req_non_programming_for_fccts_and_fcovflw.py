"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.


NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 60062
version: 3
title: N_Br Performance requirement in non-programming session for FC.CTS and FC.OVFLW

purpose: >
    The time spent waiting shall be minimized. Although N_Br time does not affect
    the transmission time as much as N_Cs time, the diagnostic kernel scheduling shall
    still be done with the same frequency.

description: >
    N_Br shall be N_Br < 20 ms for FC.CTS and FC.OVFLW when in non-programming session.

    Note:
    a. If other CAN frames with higher priority exist on CAN, then a FC N_PDU
    may be delayed due to CAN protocol arbitration. The requirement is applicable
    and verifiable only when no such frame exist.
    b. For a client side of a gateway sending parallel requests, the CAN frames
    will have different CAN identifiers and hence different priority, and actual N_Cs
    may be higher than the requirement, this is expected.
    c. For a server, if other servers are sending responses in parallel then a FC N_PDU
    may be delayed due to CAN protocol arbitration, this is expected.
    d. The Autosar CAN Transport Layer configuration parameter CanTpNbr is not configuring
    the N_Br performance for the first transmitted FlowControl after a FirstFrame although
    CanTpNbr is stated to be a performance configuration parameter. Instead CanTpNbr is
    configuring an internal timeout of getting internal buffer resources for use in subsequent
    reception of Consecutive Frames and affect the time between a previous FlowControl and
    a subsequent FlowControl.

details: >
    Verify N_Br is less than 20 ms for FC.CTS and FC.OVFLW in non-programming session.
    Steps:
    1. Verify the response from ECU by sending UDS request with message sizes-1020 and 1025 bytes
    2. Receive the flow control frame FC.CTS and FC.OVFLW
    3. Capture the difference of CAN frame send and receive timestamps to find N_Br
    4. Verify N_Br is less than 20 ms for both FC.CTS and FC.OVFLW
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.uds import UdsEmptyResponse
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_test_odtb2 import SupportTestODTB2

SC = SupportCAN()
SIO = SupportFileIO()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()


def send_multiframe_cts(dut: Dut, parameters):
    """
    Send a request with MultiFrame for FC.CTS state
    Args:
        dut (class obj): Dut instance
        parameters (dict): did, payload_max_length_cts
    Return:
        response (bool): Positive response on receiving FlowControl(FC) frame
    """
    # Create a payload with size less than 1024 bytes to send to ECU, padding the payload with '00'
    # till the size becomes 1020 bytes
    payload = SC_CARCOM.can_m_send("ReadDataByIdentifier", bytes.fromhex(parameters['did']), b'')

    while len(payload) < parameters['payload_max_length_cts']:
        payload = payload + bytes.fromhex('00')

    SC.clear_all_can_messages()
    SC.update_can_messages(dut)

    dut.uds.generic_ecu_call(payload)

    # Verify FC parameters
    logging.info("Received FC Frame: %s", SC.can_cf_received[dut["receive"]])

    fc_code = '3000' + dut.conf.default_rig_config["FC_Separation_time"]

    logging.info("Received CAN message: %s", SC.can_messages[dut["receive"]])
    logging.info("CAN MultiFrame: %s", SC.can_frames[dut["receive"]])

    if SUTE.test_message(SC.can_cf_received[dut["receive"]], teststring=fc_code):
        return True

    logging.error("ECU did not send FlowControl(FC) frame")
    return False


def send_multiframe_ovflw(dut: Dut, parameters):
    """
    Send a request with payload of size 1025 bytes for FC.OVFLW
    Args:
        dut (class obj): Dut instance
        parameters (dict): did, payload_max_length_ovflw
    Return:
        response (bool): Positive response on receiving FlowControl(FC) frame
    """
    # Create a payload with size greater than 1024 bytes to send to ECU, padding the payload with
    # '00' till the size becomes 1025 bytes
    payload = SC_CARCOM.can_m_send("ReadDataByIdentifier", bytes.fromhex(parameters['did']), b'')

    while len(payload) < parameters['payload_max_length_ovflw']:
        payload = payload + bytes.fromhex('00')

    SC.clear_all_can_messages()
    SC.update_can_messages(dut)

    try:
        dut.uds.generic_ecu_call(payload)
    except UdsEmptyResponse:
        pass

    # Verify FC parameters
    logging.info("Received FC Frame: %s", SC.can_cf_received[dut["receive"]])
    logging.info("Received CAN message: %s", SC.can_messages[dut["receive"]])
    logging.info("CAN MultiFrame: %s", SC.can_frames[dut["receive"]])

    fc_code_ovflw = '3200' + dut.conf.default_rig_config["FC_Separation_time"]

    if SUTE.test_message(SC.can_cf_received[dut["receive"]], teststring=fc_code_ovflw):
        return True

    logging.error("ECU did not send 3200 FC.OVFLW message")
    return False


def derive_nbr_time(dut: Dut, parameters):
    """
    Derive N_Br_time based on sent and received frame timestamps
    Args:
        dut (class obj): Dut instance
        parameters (dict): time
    Returns:
        result (bool): True if N_Br time is less then 20 ms
    """
    time_stamp = [0]

    # Send first frame
    time_stamp[0] = SC.can_frames[dut["send"]][0][0]
    # Receive flow control frame
    time_stamp.append(SC.can_cf_received[dut["receive"]][0][0])

    nbr_time = round(1000 * (time_stamp[1] - time_stamp[0]), 3)
    # Check N_Br time- FF-FC.CTS/ FC.OVFLW is less than 20ms
    result = nbr_time < parameters['time']
    return result, nbr_time


def step_1(dut: Dut, parameters):
    """
    action: Verify N_Br is less than 20 ms for FC.CTS in default session
    expected_result: Positive response on successfully verified N_Br time
    """
    # Send a request with payload size less than 1024 bytes to test ECU response for FC.CTS
    cts_result = send_multiframe_cts(dut, parameters)
    if cts_result:
        nbr_result, nbr_time = derive_nbr_time(dut, parameters)
        # Verify N_Br is less than 20 ms
        if nbr_result:
            logging.info("N_Br time %sms is less than 20ms for FC.CTS in default session ",
                         nbr_time)
            return True
        logging.error("Test Failed: N_Br time %sms is greater than 20ms for FC.CTS in default"
                      " session", nbr_time)
        return False

    logging.error("Test Failed: ECU did not send FlowControl(FC) frame")
    return False


def step_2(dut: Dut, parameters):
    """
    action: Verify N_Br is less than 20 ms for FC.OVFLW in default session
    expected_result: Positive response on successfully verified N_Br time
    """
    # Send a request with payload size greater than 1024 bytes to test ECU response for FC.OVFLW
    ovflw_result = send_multiframe_ovflw(dut, parameters)
    if ovflw_result:
        # Verify N_Br is less than 20 ms
        nbr_result, nbr_time = derive_nbr_time(dut, parameters)
        if nbr_result:
            logging.info("N_Br time %sms is less than 20ms for FC.OVFLW in default session",
                         nbr_time)
            return True
        logging.error("Test Failed: N_Br time %sms is greater than 20ms for FC.OVFLW in default"
                      " session", nbr_time)
        return False

    logging.error("Test Failed: ECU did not send 3200 FC.OVFLW message")
    return False


def step_3(dut: Dut, parameters):
    """
    action: Verify N_Br is less than 20 ms for FC.CTS in extended session
    expected_result: Positive response on successfully verified N_Br time
    """
    # Set to extended session
    dut.uds.set_mode(3)

    # Send a request with payload size less than 1024 bytes to test ECU response for FC.CTS
    cts_result = send_multiframe_cts(dut, parameters)
    if cts_result:
        nbr_result, nbr_time = derive_nbr_time(dut, parameters)
        # Verify N_Br is less than 20 ms
        if nbr_result:
            logging.info("N_Br time %sms is less than 20ms for FC.CTS in extended session ",
                         nbr_time)
            return True
        logging.error("Test Failed: N_Br time %sms is greater than 20ms for FC.CTS in extended"
                      " session", nbr_time)
        return False

    logging.error("Test Failed: ECU did not send FlowControl(FC) frame")
    return False


def step_4(dut: Dut, parameters):
    """
    action: Verify N_Br is less than 20 ms for FC.OVFLW in extended session
    expected_result: Positive response on successfully verified N_Br time
    """
    # Send a request with payload size greater than 1024 bytes to test ECU response for FC.OVFLW
    ovflw_result = send_multiframe_ovflw(dut, parameters)
    if ovflw_result:
        # Verify N_Br is less than 20 ms
        nbr_result, nbr_time = derive_nbr_time(dut, parameters)
        if nbr_result:
            logging.info("N_Br time %sms is less than 20ms for FC.OVFLW in extended session",
                         nbr_time)
            return True
        logging.error("Test Failed: N_Br time %sms is greater than 20ms for FC.OVFLW in extended"
                      " session", nbr_time)
        return False

    logging.error("Test Failed: ECU did not send 3200 FC.OVFLW message")
    return False


def run():
    """
    Verify N_Br time is less than 20 ms for FC.CTS and FC.OVFLW in non-programming session
    (default/extended)
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'did': '',
                       'payload_max_length_cts': 0,
                       'payload_max_length_ovflw': 0,
                       'time': 0}
    try:
        dut.precondition(timeout=90)
        # Read yml parameters
        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters, purpose="Verify N_Br is less than 20 ms for"
                                                           " FC.CTS in default session")
        if result_step:
            result_step = dut.step(step_2, parameters, purpose="Verify N_Br is less than 20 ms for"
                                                               " FC.OVFLW in default session")
        if result_step:
            result_step = dut.step(step_3, parameters, purpose="Verify N_Br is less than 20 ms for"
                                                               " FC.CTS in extended session")
        if result_step:
            result_step = dut.step(step_4, parameters, purpose="Verify N_Br is less than 20 ms for"
                                                               " FC.OVFLW in extended session")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
