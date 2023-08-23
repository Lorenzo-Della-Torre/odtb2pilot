"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 60008
version: 2
title: BlockSize parameter programming session- server and client side
purpose: >
    Define BlockSize for programming session server side. For more information see section
    BlockSize (BS) parameter definition.

description: >
    In programming session the receiver must respond with a BS value that does not generate more
    than one FlowControl (FC) N_PDU (including the first FC N_PDU) per 4095 bytes of data for a
    complete transaction.

details: >
    Verify FlowControl(FC) response in programming session by sending UDS request with 4065 bytes
    and 4094 bytes
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.uds import UdsEmptyResponse
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_can import SupportCAN, CanTestExtra, CanPayload
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO

SUTE = SupportTestODTB2()
SC = SupportCAN()
SC_CARCOM = SupportCARCOM()
SIO = SupportFileIO()


def prepare_payload(programming_did, payload_length):
    """
    Prepare payload with programming DID to send to the ECU
    Args:
        programming_did (str): Programming DID
        payload_length (int): Payload maximum length
    Returns:
        payload (bytes): Padded payload
    """
    payload = bytes.fromhex(programming_did)

    # Padding the payload with 0x00 till the size becomes payload_length
    while len(payload) < payload_length:
        payload = payload + bytes.fromhex('00')

    return payload


def read_did_and_verify(dut, did_to_read, payload_length, response_flag=False):
    """
    Verify ReadDataByIdentifier service 22 with programming DID
    Args:
        dut (Dut): An instance of Dut
        did_to_read (str): programming DID
        payload_length (int): Payload maximum length
        response_flag (bool): Check positive response when true
    Returns:
        (bool): True on successfully verified response
    """
    payload = prepare_payload(did_to_read, payload_length)

    cpay: CanPayload = {"payload": SC_CARCOM.can_m_send("ReadDataByIdentifier", payload, b''),
                        "extra": ''}

    etp: CanTestExtra = {"step_no" : 111,
                         "purpose" : "send DID request - requires MF to send",
                         "timeout" : 4, # wait for message to arrive, but don't test (-1)
                         "min_no_messages" : -1,
                         "max_no_messages" : -1}

    result = SUTE.teststep(dut, cpay, etp)
    logging.info("Result after CAN send %s", result)

    response = SC.can_messages[dut["receive"]][0][2]

    if response_flag:
        if response[4:6] == '62':
            # Verify if expected DID is present in reply
            result = SUTE.test_message(SC.can_messages[dut["receive"]], teststring='F125')
            if not result:
                logging.error("Test Failed: Expected DID %s to be present in response,"
                              " received %s", did_to_read, SC.can_messages[dut["receive"]])
                return False

            logging.info("Received positive response %s for request ReadDataByIdentifier as"
                         " expected", response[4:6])
            return True

        logging.error("Test Failed: Expected positive response, received %s", response)
        return False

    if response[2:4] == '7F' and response[6:8] == '13':
        logging.info("Received NRC %s for request ReadDataByIdentifier as expected",
                      response[6:8])
        return True

    logging.error("Test Failed: Expected NRC '13', received %s", response)
    return False


def verify_fc_overflow(dut, did_to_read, payload_length):
    """
    Verify flow control overflow with payload of size 4094 bytes
    Args:
        dut (Dut): An instance of Dut
        did_to_read (str): Programming DID
        payload_length (int): Payload maximum length
    Return:
        response (bool): True when FlowControl(FC) overflow frame received
    """
    payload = prepare_payload(did_to_read, payload_length)

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

    fc_code_ovflw = '3200'

    if SUTE.test_message(SC.can_cf_received[dut["receive"]], teststring=fc_code_ovflw):
        return True

    logging.error("Test Failed: ECU did not send 3200 FC.OVFLW message")
    return False


def verify_flowcontrol_message(dut, parameters, payload_length, response_flag):
    """
    Verify flow control message for a multiframe request with payload size 4065 bytes
    Args:
        dut (Dut): An instance of Dut
        parameters (dict): Programming DID
        payload_length (int): Payload maximum length
        response_flag (bool): True for positive response
    Return:
        response (bool): True when flow control(FC) response is received
    """
    # Request DID in one request and verify if DID is included in response
    result_non_prog_dids = read_did_and_verify(dut, parameters['prog_did'],
                                               payload_length, response_flag)
    if not result_non_prog_dids:
        return False

    # Verify FC parameters
    fc_code = '3000'

    if not SUTE.test_message(SC.can_cf_received[dut["receive"]], teststring=fc_code):
        logging.error("Test Failed: ECU did not send FlowControl(FC) frame")
        return False

    return True


def verify_flowcontrol_response_30(dut, parameters):
    """
    Verify FlowControl(FC) response with payload 4065 bytes
    Args:
        dut (Dut): An instance of Dut
        parameters (dict): Programming DID and payload lengths
    Return:
        response (bool): True when FlowControl(FC) response verified
    """
    result_negative_response = verify_flowcontrol_message(dut,
                               parameters, payload_length=parameters['pl_size_fc_30'],
                               response_flag=False)
    if not result_negative_response:
        logging.error("Test Failed: Expected NRC-13 and frame control(FC) is not received")
        return False

    return True


def verify_flowcontrol_response_32(dut, parameters):
    """
    Verify FlowControl(FC) response with payload 4094 bytes
    Args:
        dut (Dut): An instance of Dut
        parameters (dict): Programming DID and payload lengths
    Return:
        response (bool): True when FlowControl(FC) response verified
    """
    # According to SWRS maximum byte value size should be 4095 bytes, but from ECU we are
    #  getting FC-Overflow(32) in the range 4066 bytes to 4094 bytes.
    result_non_prog_dids = verify_fc_overflow(dut, parameters['prog_did'],
                           payload_length=parameters['pl_size_fc_32'])
    if not result_non_prog_dids:
        return False

    return True


def step_1(dut: Dut, parameters):
    """
    action: Set ECU in programming session and verify ReadDataByIdentifier service 22 with DID
            'F125' in programming session
    expected_result: DID in the request should be included in the ECU response
    """
    # Set to programming session
    dut.uds.set_mode(2)
    dut.uds.set_mode(2)
    dut.uds.set_mode(2)
    # Verify active diagnostic session
    result = dut.uds.active_diag_session_f186()
    print(f"THE RESULT IS {result}")
    if result.data['details']['mode'] != 2:
        logging.error("Test Failed: ECU is not in programming session")
        return False

    result = read_did_and_verify(dut, parameters['prog_did'], payload_length=0, response_flag=True)
    if not result:
        return False

    return True


def step_2(dut: Dut, parameters):
    """
    action: Verify FlowControl(FC) in programming session with payload 4065 bytes
    expected_result: ECU should give NRC-13 for payload 4065 bytes and FlowControl(FC) response
                     should be successfully verified in programming session
    """
    result = verify_flowcontrol_response_30(dut, parameters)
    if not result:
        logging.error("Test Failed: FlowControl(FC) response is not received as expected in"
                      " programming session")
        return False

    return True


def step_3(dut: Dut, parameters):
    """
    action: Verify FlowControl(FC) in programming session with payload 4094 bytes
    expected_result: FlowControl(FC) response should be successfully verified in programming
                     session
    """
    result = verify_flowcontrol_response_32(dut, parameters)
    if not result:
        logging.error("Test Failed: FlowControl(FC) response is not received as expected in"
                      " programming session")
        return False

    return True


def run():
    """
    Verify FlowControl(FC) response in programming session by sending UDS request with 4065 bytes
    and 4094 bytes
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'prog_did': '',
                       'pl_size_fc_30': 0,
                       'pl_size_fc_32': 0}
    try:
        dut.precondition(timeout=60)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters, purpose='Set ECU in extended session and'
                               ' verify ReadDataByIdentifier service 22 with DID F125 in'
                               ' programming session')
        if result_step:
            result_step = dut.step(step_2, parameters, purpose='Verify'
                                   ' FlowControl(FC) in programming session with payload'
                                   ' 4065 bytes')
        if result_step:
            result_step = dut.step(step_3, parameters, purpose='Verify'
                                   ' FlowControl(FC) in programming session with payload'
                                   ' 4094 bytes')
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
