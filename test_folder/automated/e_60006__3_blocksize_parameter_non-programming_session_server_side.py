"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 60006
version: 3
title: BlockSize parameter non-programming session server side
purpose: >
    Define BlockSize for non-programming session server side. For more information see section
    BlockSize (BS) parameter definition

description: >
    In non-programming session the receiver must respond with a BS value that does not generate
    more than one FlowControl (FC) N_PDU (including the first FC N_PDU) per 300 bytes of data for
    a complete transaction.

details: >
    Verify that the FlowControl (FC) is sent as required in both default and extended session
    (non-programming session) by sending UDS request with 13 bytes, 300 bytes and 1026 bytes.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.uds import UdsEmptyResponse
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO

SUTE = SupportTestODTB2()
SC = SupportCAN()
SC_CARCOM = SupportCARCOM()
SIO = SupportFileIO()


def prepare_payload(did_list, pl_max_length, payload_type):
    """
    Create a payload with multiple DIDs to send to the ECU
    Args:
        did_list (list): DIDs
        pl_max_length (int): Payload maximum length
        payload_type (str): Type of payload
    Returns:
        payload (bytes): Read data by id padded payload
    """
    dids_str = ''.join(did_list)

    if payload_type == 'overflow':
        # Create a payload with size greater than 1024 bytes to send to ECU, padding the payload
        # with '00' till the size becomes 1025 bytes
        payload = SC_CARCOM.can_m_send("ReadDataByIdentifier", bytes.fromhex(dids_str), b'')
    else:
        # Padding the payload with 0x00 till the size becomes pl_max_length
        payload = bytes.fromhex(dids_str)

    while len(payload) < pl_max_length:
        payload = payload + bytes.fromhex('00')

    return payload


def find_did(did_list, response):
    """
    Verify DIDs are present in ECU response
    Args:
        did_list (list): DIDs
        response (str): ECU response
    Returns:
        (bool): True when all DIDs are present
    """
    results = []
    for did in did_list:
        did_find_pos = response.find(did)
        if did_find_pos == -1:
            logging.error("%s DID not found in ECU response", did)
            results.append(False)
        else:
            results.append(True)

    if all(results) and len(results) != 0:
        logging.info("Successfully verified that all the DIDs are present in ECU response")
        return True

    logging.error("Test Failed: Some DIDs are not present in ECU response")
    return False


def request_read_data_by_id(dut, dids_to_read, pl_max_length, flag=False):
    """
    Verify ReadDataByIdentifier service 22 with multiple DIDs
    Args:
        dut (Dut): An instance of Dut
        dids_to_read (list): DIDs
        pl_max_length (int): Payload maximum length
        flag (bool): Check positive response when true
    Returns:
        (bool): True on successfully verified response
    """
    payload = prepare_payload(dids_to_read, pl_max_length, payload_type='not overflow')
    response = dut.uds.read_data_by_id_22(payload)

    if flag:
        if response.raw[4:6] == '62':
            # Check if expected DIDs are present in reply
            result = find_did(dids_to_read, response.raw)
            if not result:
                return False

            logging.info("Received positive response %s for request ReadDataByIdentifier",
                        response.raw[4:6])
            return True

        logging.error("Test Failed: Expected positive response, received %s", response.raw)
        return False

    if response.raw[2:4] == '7F' and response.raw[6:8] == '13':
        logging.info("Received NRC %s for request ReadDataByIdentifier as expected",
                      response.raw[6:8])
        return True

    logging.error("Test Failed: Expected NRC '13', received %s", response.raw)
    return False


def send_multiframe_cts(dut):
    """
    Send a request with MultiFrame for FC.CTS state
    Args:
        dut (class obj): Dut instance
    Return:
        response (bool): Positive response on receiving FlowControl(FC) frame
    """
    # Verify FC parameters
    logging.info("Received FC Frame: %s", SC.can_cf_received[dut["receive"]])

    fc_code = '3000' + dut.conf.default_rig_config["FC_Separation_time"]
    logging.info("CAN MultiFrame: %s", SC.can_frames[dut["receive"]])

    if SUTE.test_message(SC.can_cf_received[dut["receive"]], teststring=fc_code):
        return True

    logging.error("Test Failed: ECU did not send FlowControl(FC) frame")
    return False


def send_multiframe_overflow(dut, dids_to_read, pl_max_length):
    """
    Send a request with payload of size 1025 bytes for FC.OVFLW
    Args:
        dut (class obj): Dut instance
        dids_to_read (list): DIDs
        pl_max_length (int): Payload maximum length
    Return:
        response (bool): Positive response on receiving FlowControl(FC) frame
    """
    payload = prepare_payload(dids_to_read, pl_max_length, payload_type='overflow')

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

    logging.error("Test Failed: ECU did not send 3200 FC.OVFLW message")
    return False


def verify_flowcontrol_message(dut, parameters, pl_max_length, flag):
    """
    Verify frame control message for a multiframe request with payload size 1byte, 13 bytes
    and 300 bytes
    Args:
        dut (class obj): Dut instance
        parameters (dict): non_prog_dids
        pl_max_length (int): Payload maximum length
        flag (bool): Check overflow when false
    Return:
        response (bool): True when all the DIDs in the request are included in the reply and
                         frame control(FC) is sent back
    """
    # Request multiple DIDs in one request and verify if DIDs are included in response
    result_non_prog_dids = request_read_data_by_id(dut, parameters['non_prog_dids'],
                           pl_max_length, flag)
    if not result_non_prog_dids:
        return False

    # Verify FC parameters
    verify_fc_parameters = send_multiframe_cts(dut)
    if not verify_fc_parameters:
        return False

    return True


def flowcontrol_response(dut, parameters):
    """
    Verify that the FlowControl (FC) is sent as required by sending UDS request with 13 bytes,
    300 bytes and 1026 bytes
    Args:
        dut (class obj): Dut instance
        parameters (dict): non_prog_dids
    Return:
        response (bool): True when FlowControl (FC) is sent as required
    """
    result = verify_flowcontrol_message(dut, parameters, pl_max_length=0, flag=True)
    if not result:
        logging.error("Test Failed: Some or all the DIDs in the request are not included in the"
                      " reply and frame control(FC) is not sent back")
        return False

    result = result and verify_flowcontrol_message(dut, parameters,
             pl_max_length=parameters['pl_size_for_positive_response'], flag=True)
    if not result:
        logging.error("Test Failed: Some or all the DIDs in the request are not included in the"
                      " reply and frame control(FC) is not sent back")
        return False

    result = result and verify_flowcontrol_message(dut, parameters,
             pl_max_length=parameters['pl_size_for_negative_response'], flag=False)
    if not result:
        logging.error("Test Failed: Expected NRC-13 and frame control(FC) is not sent back")
        return False

    result_non_prog_dids = result and send_multiframe_overflow(dut, parameters['non_prog_dids'],
                           pl_max_length=parameters['pl_size_for_overflow'])
    if not result_non_prog_dids:
        return False

    return True


def step_1(dut: Dut, parameters):
    """
    action: Verify that the FlowControl (FC) is sent as required by sending UDS request with 13
            bytes, 300 bytes and 1026 bytes for default session
    expected_result: True when FlowControl (FC) is sent as required in default session
    """
    result = flowcontrol_response(dut, parameters)
    if not result:
        logging.error("Test Failed: FlowControl (FC) is not sent as required in default session")
        return False
    return True


def step_2(dut: Dut):
    """
    action: Set and verify that the ECU is in extended session
    expected_result: True when ECU is in extended session
    """
    dut.uds.set_mode(3)
    result = dut.uds.active_diag_session_f186()
    if result.data['details']['mode'] != 3:
        logging.error("ECU is not in extended session")
        return False

    logging.info("ECU is in extended session as expected")
    return True


def step_3(dut: Dut, parameters):
    """
    action: Verify that the FlowControl (FC) is sent as required by sending UDS request with 13
            bytes, 300 bytes and 1026 bytes for extended session
    expected_result: True when FlowControl (FC) is sent as required in extended session
    """
    result = flowcontrol_response(dut, parameters)
    if not result:
        logging.error("Test Failed: FlowControl (FC) is not sent as required in extended session")
        return False
    return True


def run():
    """
    Verify that the FlowControl (FC) is sent as required in both default and extended session
    (non-programming session) by sending UDS request with 13 bytes, 300 bytes and 1026 bytes.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'non_prog_dids':'',
                       'pl_size_for_positive_response': 0,
                       'pl_size_for_negative_response': 0,
                       'pl_size_for_overflow': 0,}
    try:
        dut.precondition(timeout=70)
        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters, purpose='Verify that the FlowControl (FC) is'
                                                           ' sent as required by sending UDS'
                                                           ' request with 13 bytes, 300 bytes'
                                                           ' and 1026 bytes for default Session')
        if result_step:
            result_step = dut.step(step_2, purpose='Set and verify that the ECU is in extended'
                                                   ' session')
        if result_step:
            result_step = dut.step(step_3, parameters, purpose='Verify that the FlowControl (FC)'
                                                               ' is sent as required by sending'
                                                               ' UDS request with 13 bytes, 300'
                                                               ' bytes and 1026 bytes for extended'
                                                               ' session')
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
