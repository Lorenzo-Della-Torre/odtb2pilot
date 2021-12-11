"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

"""
reqprod:  60006
version:  3
title:    BlockSize parameter non-programming session server side
purpose: >
    Define BlockSize for non-programming session server side.
    For more information see section BlockSize (BS) parameter definition

description: >
    In non-programming session the receiver must respond with a
    BS value that does not generate more than one FlowControl (FC) N_PDU
    (including the first FC N_PDU) per 300 bytes of data for a complete transaction.


details: >
    Verify the response from ECU by sending UDS request with different
    message sizes such as 13bytes, 300 bytes and 301 bytes.
    Verify that the flow control is sent from the ECU as required.
"""

import sys
import logging
import inspect

from hilding.dut import Dut
from hilding.dut import DutTestError

from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_can import SupportCAN, CanTestExtra, CanPayload
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO

SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
SIO = SupportFileIO()

def step_1(dut: Dut):
    """
    action:
        Verify that the ECU is in Default Session
        using DID 0xF186

    expected_result:
        The ECU is in Default session.
    """
    res = dut.uds.active_diag_session_f186()
    logging.debug(res)
    if res.data['details']['mode'] != 1:
        raise DutTestError(
            f"ECU is not in Default Session:\n{res}")

def step_2(dut: Dut):
    """
    action:
        send a request with MultiFrame and test if
        DIDs are included in the reply from the ECU.

    expected_result:
        Message is received by the ECU and Framecontrol(FC) is sent back.
        All the DIDs in the request should be included in the reply.
    """

    #Create a payload with multiple DIDs to send to te ECU.
    payload = b'\xDD\x02\xDD\x0A\xDD\x0B\x49\x47'
    test_string = '3000'

    res = dut.uds.read_data_by_id_22(payload)
    logging.debug(res)

    # verify FC parameters from ECU for block_size
    logging.debug("FC parameters used:")
    logging.debug("FC frame count: %s", len(SC.can_cf_received[dut["receive"]]))
    logging.info("FC Frame: %s", SC.can_cf_received[dut["receive"]])

    test_string = test_string + dut.conf.platforms[\
                dut.conf.rig.platform]['FC_Separation_time']

    if not SUTE.test_message(SC.can_cf_received[dut["receive"]], teststring=test_string):
        raise DutTestError("ECU did not sent Flow Control(FC) Frame\n")

    logging.debug("Number of Messages received: %s",len(SC.can_messages[dut["receive"]]))
    logging.info("Messages: %s",SC.can_messages[dut["receive"]])
    logging.debug("Number of frames received: %s", len(SC.can_frames[dut["receive"]]))
    logging.info("Frames: %s", SC.can_frames[dut["receive"]])
    logging.info("Test if message string contains all DIDs expected\n")

    if not ('4947' in res.raw and 'DD0A' in res.raw and'DD0B' in res.raw and'DD02' in res.raw):
        raise DutTestError(
            f"Proper response not received from ECU, one or more DIDs\
                not present in the response from the ECU\n{res.raw}")

def step_3(dut: Dut):
    """
    action:
        Build a longer message (payload 13 bytes), send it
        and test id DIDs are included in the reply.


    expected_result:
        Message is received by the ECU and Framecontrol(FC) message is sent back.
        All the DIDs in the request should be included in the reply.
    """

    #Create a payload with multiple DIDs to send to te ECU.
    payload = b'\xDD\x02\xDD\x0A\xDD\x0B\x49\x47'
    pl_max_length = 12
    test_string = '3000'

    #Padding the payload with 0x00 till the size becomes pl_max_length
    while len(payload) < pl_max_length:
        payload = payload + b'\x00'

    res = dut.uds.read_data_by_id_22(payload)
    logging.debug(res)

    # verify FC parameters from ECU for block_size
    logging.debug("FC parameters used:")
    logging.debug("FC frame count: %s", len(SC.can_cf_received[dut["receive"]]))
    logging.info("FC Frame: %s", SC.can_cf_received[dut["receive"]])

    test_string = test_string + dut.conf.platforms[\
                dut.conf.rig.platform]['FC_Separation_time']

    if not SUTE.test_message(SC.can_cf_received[dut["receive"]], teststring=test_string):
        raise DutTestError("ECU did not sent Flow Control(FC) Frame\n")

    logging.debug("Number of messages received: %s",len(SC.can_messages[dut["receive"]]))
    logging.info("Messages: %s",SC.can_messages[dut["receive"]])
    logging.debug("Number of frames received: %s", len(SC.can_frames[dut["receive"]]))
    logging.info("Frames: %s", SC.can_frames[dut["receive"]])
    logging.info("Test if message string contains all DIDs expected\n")

    if not ('4947' in res.raw and 'DD0A' in res.raw and'DD0B' in res.raw and'DD02' in res.raw):
        raise DutTestError(
            f"Proper response not received from ECU for 13 bytes payload, one or more DIDs\
                 not present in the response from the ECU \n{res.raw}")

def step_4(dut: Dut):
    """
    action:
        Build a longer message (payload 300 bytes), send it
        and test id DIDs are included in the reply.


    expected_result:
        Message is received by the ECU and Framecontrol(FC) message is sent back.
        NRC is sent by the ECU as a response,
    """

    #Create a payload with multiple DIDs to send to te ECU.
    payload = b'\xDD\x02\xDD\x0A\xDD\x0B\x49\x47'
    pl_max_length = 299
    test_string = '3000'

    #Padding the payload with 0x00 till the size becomes pl_max_length
    while len(payload) < pl_max_length:
        payload = payload + b'\x00'

    res = dut.uds.read_data_by_id_22(payload)
    logging.debug(res)

    # verify FC parameters from ECU for block_size
    logging.debug("FC parameters used:")
    logging.debug("FC frame count: %s", len(SC.can_cf_received[dut["receive"]]))
    logging.info("FC Frame: %s", SC.can_cf_received[dut["receive"]])

    test_string = test_string + dut.conf.platforms[\
                dut.conf.rig.platform]['FC_Separation_time']

    if not SUTE.test_message(SC.can_cf_received[dut["receive"]], teststring=test_string):
        raise DutTestError("ECU did not sent Flow Control(FC) Frame\n")

    logging.debug("Number of messages received: %s",len(SC.can_messages[dut["receive"]]))
    logging.info("Messages: %s",SC.can_messages[dut["receive"]])
    logging.debug("Number of frames received: %s", len(SC.can_frames[dut["receive"]]))
    logging.info("Frames: %s", SC.can_frames[dut["receive"]])
    logging.info("Test if string contains all DIDs expected\n")

    # Expecting a NRC13-incorrectMessageLengthOrInvalidFormat
    # or NRC31-requestOutOfRange from ECU in this case of 22 Service. This means that we
    # get a response either from ECU and not a FC frame as 22 service responds with an NRC
    # when a long message is sent.
    if not ('7F2213' in res.raw or '7F2231' in res.raw ):
        raise DutTestError(
            f"Expected NRC not received from ECU for ReadDID with 300 bytes payload\n{res.raw}")

def step_5(dut: Dut):
    """
    action:
        Build an even longer message (payload 301 bytes), send it
        and test if there is any reply from ECU.


    expected_result:
        First Message is received by the ECU and Framecontrol message(FC code 32) is sent back.
        The rest of the Message is aborted.
    """

    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                        b'\xDD\x02\xDD\x0B\xDD\x0C\x49\x47',
                                        b''),
        "extra": ''
        }
    # Parameters for the teststep
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    etp: CanTestExtra = {
        "step_no" : 8,
        "purpose" : "send several requests at one time - requires MultiFrame to send",
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    pl_max_length = 300
    test_string = '3200'

    #Padding the payload with 0x00 till the size becomes pl_max_length
    while len(cpay["payload"]) < pl_max_length:
        cpay["payload"] = cpay["payload"] + b'\x00'

    logging.info("Send message with 301 bytes payload")
    logging.info("Message: %s", cpay["payload"])

    if not SUTE.teststep(dut, cpay, etp):
        raise DutTestError("No response from ECU\n")

    # verify FC parameters from ECU for block_size
    logging.debug("FC parameters used:")
    logging.debug("FC frame count: %s", len(SC.can_cf_received[dut["receive"]]))
    logging.info("FC Frame: %s", SC.can_cf_received[dut["receive"]])

    logging.debug("Number of messages received: %s",len(SC.can_messages[dut["receive"]]))
    logging.info("Messages: %s",SC.can_messages[dut["receive"]])
    logging.debug("Number of frames received: %s", len(SC.can_frames[dut["receive"]]))
    logging.info("Frames: %s", SC.can_frames[dut["receive"]])
    logging.info("Test if FC message 32000A is received from ECU\n")

    test_string = test_string + dut.conf.platforms[\
                dut.conf.rig.platform]['FC_Separation_time']

    if not SUTE.test_message(SC.can_frames[dut["receive"]], teststring=test_string):
        raise DutTestError(
            "ECU did not send 32000A FC message when the payload exceeds the block size\n")

def run():
    """
    Verify the response from ECU by sending UDS request for different
    message sizes such as 12bytes, 298 bytes and 300 bytes.
    Verify that the flow control is sent as required
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    dut = Dut()
    start_time = dut.start()
    result = False

    try:
        # Communication with ECU lasts 30 seconds.
        dut.precondition(timeout=60)

        # Verify default session
        dut.step(step_1, purpose="Verify that the ECU is in Default Session")

        # Send a request with MultiFrame
        dut.step(step_2, purpose="Send a request with MultiFrame")

        # Build longer message (payload 13 bytes) and send it.
        dut.step(step_3, purpose="Build longer message (payload 13 bytes) and send it")

        # Build longer message (payload 300 bytes) and send it.
        dut.step(step_4, purpose="Build longer message (payload 300 bytes) and send it")

        # Build even longer message (payload 301 bytes) and send it.
        dut.step(step_5, purpose="Build even longer message (payload 301 bytes) and send it")

        result = True
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)

if __name__ == '__main__':
    run()
