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
    Verify FlowControl(FC) response in both default and extended session(non-programming session)
    by sending UDS request with 12 bytes, 300 bytes and 1025 bytes.
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


def prepare_payload(did_list, payload_length):
    """
    Prepare payload with multiple DIDs to send to the ECU
    Args:
        did_list (list):  Non programming DIDs
        payload_length (int): Payload maximum length
    Returns:
        payload (bytes): Padded payload
    """
    dids_str = ''.join(did_list)

    payload = bytes.fromhex(dids_str)

    # Padding the payload with 0x00 till the size becomes payload_length
    while len(payload) < payload_length:
        payload = payload + bytes.fromhex('00')

    return payload


def find_did(did_list, response):
    """
    Verify DIDs are present in ECU response
    Args:
        did_list (list): Non programming DIDs
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


def read_did_and_verify(dut, dids_to_read, payload_length, response_flag=False):
    """
    Verify ReadDataByIdentifier service 22 with multiple DIDs
    Args:
        dut (Dut): An instance of Dut
        dids_to_read (list): Non programming DIDs
        payload_length (int): Payload maximum length
        response_flag (bool): Check positive response when true
    Returns:
        (bool): True on successfully verified response
    """
    payload = prepare_payload(dids_to_read, payload_length)
    response = dut.uds.read_data_by_id_22(payload)

    if response_flag:
        if response.raw[4:6] == '62':
            # Verify if expected DIDs are present in reply
            result = find_did(dids_to_read, response.raw)
            if not result:
                return False

            logging.info("Received positive response %s for request ReadDataByIdentifier as"
                         " expected", response.raw[4:6])
            return True

        logging.error("Test Failed: Expected positive response, received %s", response.raw)
        return False

    if response.raw[2:4] == '7F' and response.raw[6:8] == '13':
        logging.info("Received NRC %s for request ReadDataByIdentifier as expected",
                      response.raw[6:8])
        return True

    logging.error("Test Failed: Expected NRC '13', received %s", response.raw)
    return False


def verify_fc_overflow(dut, dids_to_read, fc_separation_time, payload_length, ):
    """
    Verify flow control overflow with payload of size 1025 bytes
    Args:
        dut (Dut): Dut instance
        dids_to_read (list): Non programming DIDs
        payload_length (int): Payload maximum length
    Return:
        response (bool): True when FlowControl(FC) overflow frame received
    """
    payload = prepare_payload(dids_to_read, payload_length)

    # Append ReadDataByIdentifier service
    payload = SC_CARCOM.can_m_send("ReadDataByIdentifier", payload, b'')

    try:
        dut.uds.generic_ecu_call(payload)
    except UdsEmptyResponse:
        pass

    # Verify FC parameters
    logging.info("Received FC Frame: %s", SC.can_cf_received[dut["receive"]])
    logging.info("Received CAN message: %s", SC.can_messages[dut["receive"]])
    logging.info("CAN MultiFrame: %s", SC.can_frames[dut["receive"]])

    fc_code_ovflw = '3200' + fc_separation_time

    if SUTE.test_message(SC.can_cf_received[dut["receive"]], teststring=fc_code_ovflw):
        return True

    logging.error("Test Failed: ECU did not send 3200 FC.OVFLW message")
    return False


def verify_flowcontrol_message(dut, parameters, fc_separation_time, payload_length, response_flag):
    """
    Verify flow control message for a multiframe request with payload size 12byte, 300 bytes
    and 1025 bytes
    Args:
        dut (Dut): Dut instance
        parameters (dict): Non programming DIDs
        payload_length (int): Payload maximum length
        response_flag (bool): True for positive response
    Return:
        response (bool): True when all the DIDs in the request are included in the reply and
                         flow control(FC) response is received
    """
    # Request multiple DIDs in one request and verify if DIDs are included in response
    result_non_prog_dids = read_did_and_verify(dut, parameters['non_prog_dids'],
                                               payload_length, response_flag)
    if not result_non_prog_dids:
        return False

    fc_code = '3000' + fc_separation_time

    if not SUTE.test_message(SC.can_cf_received[dut["receive"]], teststring=fc_code):
        logging.error("Test Failed: ECU did not send FlowControl(FC) frame")
        return False

    return True


def verify_flowcontrol_response(dut, parameters, fc_separation_time):
    """
    Verify FlowControl(FC) response with payload 12 bytes, 300 bytes and 1025 bytes
    Args:
        dut (Dut): Dut instance
        parameters (dict): Non programming DIDs and payload lengths.
    Return:
        response (bool): True when FlowControl(FC) response verified
    """
    result_positive_response = verify_flowcontrol_message(dut, parameters, fc_separation_time,
                                                          payload_length=0,
                                                          response_flag=True
                                                          )
    if not result_positive_response:
        logging.error("Test Failed: Some or all the DIDs in the request are not included in the"
                      " reply and frame control(FC) is not received")
        return False

    result_positive_response = result_positive_response and\
                               verify_flowcontrol_message(dut,
                                   parameters, fc_separation_time,
                                   payload_length=parameters['pl_size_positive_response'],
                                   response_flag=True
                                   )
    if not result_positive_response:
        logging.error("Test Failed: Some or all the DIDs in the request are not included in the"
                      " reply and frame control(FC) is not received")
        return False

    result_negative_response = result_positive_response and\
                               verify_flowcontrol_message(dut,
                                   parameters, fc_separation_time,
                                   payload_length=parameters['pl_size_negative_response'],
                                   response_flag=False
                                   )
    if not result_negative_response:
        logging.error("Test Failed: Expected NRC-13 and frame control(FC) is not received")
        return False

    result_non_prog_dids = result_negative_response and\
                           verify_fc_overflow(dut,
                               parameters['non_prog_dids'],
                               fc_separation_time,
                               payload_length=parameters['pl_size_overflow']
                               )
    if not result_non_prog_dids:
        return False

    return True


def step_1(dut: Dut, parameters, fc_separation_time):
    """
    action: Verify FlowControl(FC) in default session with payload 12 bytes, 300 bytes and 1025
            bytes
    expected_result: True when FlowControl(FC) response is successfully verified in default
                     session
    """
    result = verify_flowcontrol_response(dut, parameters, fc_separation_time)
    if not result:
        logging.error("Test Failed: FlowControl(FC) response is not received as expected in"
                      " default session")
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


def step_3(dut: Dut, parameters, fc_separation_time):
    """
    action: Verify FlowControl(FC) in extended session with payload 12 bytes, 300 bytes and 1025
            bytes
    expected_result: True when FlowControl(FC) response is successfully verified in extended
                     session
    """
    result = verify_flowcontrol_response(dut, parameters, fc_separation_time)
    if not result:
        logging.error("Test Failed:FlowControl(FC) response is not received as expected in"
                      " extended session")
        return False
    return True


def run():
    """
    Verify FlowControl(FC) response in both default and extended session(non-programming session)
    by sending UDS request with 12 bytes, 300 bytes and 1025 bytes.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'non_prog_dids':'',
                       'pl_size_positive_response': 0,
                       'pl_size_negative_response': 0,
                       'pl_size_overflow': 0,}
    try:
        dut.precondition(timeout=70)
        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        fc_separation_time = '05'
        new_fc_separation_time = SIO.parameter_adopt_teststep('fc_separation_time')
        if new_fc_separation_time != '':
            assert isinstance(new_fc_separation_time, str)
        fc_separation_time = new_fc_separation_time    # Verify FC parameters
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters, fc_separation_time,
                               purpose='Verify FlowControl(FC) response in'
                                       ' default Session')
        if result_step:
            result_step = dut.step(step_2, purpose='Verify ECU is in extended session')
        if result_step:
            result_step = dut.step(step_3, parameters, fc_separation_time,
                                   purpose='Verify FlowControl(FC) response'
                                           ' in extended session')
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
