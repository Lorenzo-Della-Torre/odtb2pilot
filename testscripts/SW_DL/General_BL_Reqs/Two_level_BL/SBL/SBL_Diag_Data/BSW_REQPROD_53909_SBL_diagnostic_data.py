# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   FJANSSO8 (Fredrik Jansson)
# date:     2019-12-16
# version:  1.0
# #inspired by https://grpc.io/docs/tutorials/basic/python.html
# Copyright 2015 gRPC authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The Python implementation of the gRPC route guide client."""

import time
from datetime import datetime
import sys
import logging

import ODTB_conf
from support_can import Support_CAN
from support_test_odtb2 import Support_test_ODTB2
from support_SecAcc import Support_Security_Access
from support_SBL import Support_SBL

SC = Support_CAN()
SUTE = Support_test_ODTB2()
SUPPORT_SECURITY_ACCESS = Support_Security_Access()
SUPPORT_SBL = Support_SBL()


def precondition(stub, can_send, can_receive, can_namespace, result):
    """
    Precondition for test running:
    BECM has to be kept alive: start heartbeat
    """

    # start heartbeat, repeat every 0.8 second
    SC.start_heartbeat(stub, "MvcmFront1NMFr", "Front1CANCfg0",
                       b'\x2F\x40\xFF\xFF\xFF\xFF\xFF\xFF', 0.5)

    SC.start_periodic(stub, "Networkeptalive", True, "Vcu1ToAllFuncFront1DiagReqFrame",
                      "Front1CANCfg0", b'\x02\x3E\x80\x00\x00\x00\x00\x00', 2.0)

    # timeout = more than maxtime script takes (seconds)
    timeout = 100
    SC.subscribe_signal(stub, can_send, can_receive, can_namespace, timeout)
    #record signal we send as well
    SC.subscribe_signal(stub, can_receive, can_send, can_namespace, timeout)

    result = step_0(stub, can_send, can_receive, can_namespace, result)
    logging.info("Precondition testok: %s\n", result)
    return result

def step_0(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 0: Complete ECU Part/Serial Number(s)
    """

    step_no = 0
    purpose = "Complete ECU Part/Serial Number(s)"
    timeout = 5
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send("ReadDataByIdentifier", b'\xED\xA0', "")
    can_mr_extra = ''

    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, step_no, purpose,
                                      timeout, min_no_messages, max_no_messages)
    logging.info('%s', SUTE.PP_CombinedDID_EDA0(SC.can_messages[can_receive][0][2], title=''))
    return result


def step_1(stub, can_send, can_receive, can_namespace, result):
    '''
    Test step 1: Download and activate Secondary Boot Loader
    '''

    step_no = 1
    purpose = "Download and activate Secondary Boot Loader"
    return result and SUPPORT_SBL.SBL_Activation_Def(stub, can_send, can_receive, can_namespace,
                                                     step_no, purpose)


def step_2(stub, can_send, can_receive, can_namespace, result):
    '''
    Test step 2: Send 1 requests - requires SF to send, MF for reply
    '''
    stepno = 2
    purpose = "Send 1 request - requires SF to send"
    timeout = 5 # wait for message to arrive, but don't test (-1)
    min_no_messages = -1
    max_no_messages = -1

    # Parameters for FrameControl FC
    block_size = 0
    separation_time = 0
    frame_control_delay = 0 #no wait
    frame_control_flag = 48 #continue send
    frame_control_auto = False

    can_m_send = SC.can_m_send("ReadDataByIdentifier", b'\xF1\x22', "")
    can_mr_extra = ''

    SC.change_MF_FC(can_send, block_size, separation_time, frame_control_delay, frame_control_flag,
                    frame_control_auto)

    return result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send, can_receive,
                                    can_namespace, stepno, purpose, timeout, min_no_messages,
                                    max_no_messages)


def step_3(can_receive, result):
    '''
    Test step 3: Test if DIDs are included in reply. In our test case we request Complete
    ECU Part/Serial Number
    '''
    stepno = 3
    purpose = "Test if requested DID are included in reply"
    SUTE.print_test_purpose(stepno, purpose)

    time.sleep(1)
    SC.clear_all_can_messages()
    logging.info("All can messages cleared")
    SC.update_can_messages(can_receive)
    logging.info("All can messages updated")
    logging.info("Step 3: messages received %s", len(SC.can_messages[can_receive]))
    logging.info("Step 3: messages: %s", SC.can_messages[can_receive])
    logging.info("Step 3: frames received %s", len(SC.can_frames[can_receive]))
    logging.info("Step 3: frames: %s", SC.can_frames[can_receive])

    sbl_diagnostic_db_part_number = SC.can_frames[can_receive][0][2].upper()
    logging.debug('Secondary Bootloader Diagnostic Database Part Number: %s',
                  sbl_diagnostic_db_part_number)
    logging.info("Test if string contains all IDs expected:")

    return result and SUTE.test_message(SC.can_messages[can_receive], teststring='F122'),\
        sbl_diagnostic_db_part_number


def step_4(stub, can_send, can_receive, can_namespace, result):
    '''
    Send several requests at one time - requires SF to send, MF for reply
    '''
    stepno = 4
    purpose = "Send several requests at one time - requires SF to send"
    timeout = 1 # wait for message to arrive, but don't test (-1)
    min_no_messages = -1
    max_no_messages = -1

    # Parameters for FrameControl FC
    block_size = 0
    separation_time = 0
    frame_control_delay = 0 #no wait
    frame_control_flag = 48 #continue send
    frame_control_auto = False

    can_m_send = SC.can_m_send("ReadDataByIdentifier", b'\xF1\x21\xF1\x2A', "")
    can_mr_extra = ''

    SC.change_MF_FC(can_send, block_size, separation_time, frame_control_delay, frame_control_flag,
                    frame_control_auto)

    return result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send, can_receive,
                                    can_namespace, stepno, purpose, timeout, min_no_messages,
                                    max_no_messages)


def step_5(can_receive, result):
    '''
    Verify if number for requests limited in programming session
    '''
    stepno = 5
    purpose = "Verify if number for requests limited in programming session"

    # No normal teststep done, instead: update CAN messages, verify all serial-numbers received
    # (by checking ID for each serial-number)
    SUTE.print_test_purpose(stepno, purpose)

    time.sleep(1)
    SC.clear_all_can_messages()
    logging.info("All can messages cleared")
    SC.update_can_messages(can_receive)
    logging.info("All can messages updated")
    logging.info("Step5: Messages received %s", len(SC.can_messages[can_receive]))
    logging.info("Step5: Messages: %s \n", SC.can_messages[can_receive])
    logging.info("Step5: Frames received %s", len(SC.can_frames[can_receive]))
    logging.info("Step5: Frames: %s \n", SC.can_frames[can_receive])
    logging.info("Test if string contains all IDs expected:")

    result = result and SUTE.test_message(SC.can_messages[can_receive],\
        teststring='037F223100000000')
    logging.debug(SUTE.PP_Decode_7F_response(SC.can_frames[can_receive][0][2]))
    return result


def step_6(stub, can_send, can_receive, can_namespace, result):
    '''
    Test step 6: Verify that we are still on SBL reading out the same SW serial number as in step 3
                 Send 1 requests - requires SF to send, MF for reply
    '''
    stepno = 6
    purpose = "Send 1 requests - requires SF to send, MF for reply"
    timeout = 5 # wait for message to arrive, but don't test (-1)
    min_no_messages = -1
    max_no_messages = -1

    # Parameters for FrameControl FC
    block_size = 0
    separation_time = 0
    frame_control_delay = 0 #no wait
    frame_control_flag = 48 #continue send
    frame_control_auto = False

    can_m_send = SC.can_m_send("ReadDataByIdentifier", b'\xF1\x22', "")
    can_mr_extra = ''

    SC.change_MF_FC(can_send, block_size, separation_time, frame_control_delay, frame_control_flag,
                    frame_control_auto)

    return result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send, can_receive,
                                    can_namespace, stepno, purpose, timeout, min_no_messages,
                                    max_no_messages)


def step_7(can_receive, result, sbl_diagnostic_db_part_number):
    '''
    Test step 7: Verify that we are still on SBL reading out the same SW serial number as in step 3
                 Test if DIDs are included in reply. In our test case we request Complete
                 ECU Part/Serial Number
    '''
    stepno = 7
    purpose = "Verify that we are still on SBL reading out the same SW serial number as in step 3"
    SUTE.print_test_purpose(stepno, purpose)

    time.sleep(1)
    SC.clear_all_can_messages()
    logging.info("All can messages cleared")
    SC.update_can_messages(can_receive)
    logging.info("All can messages updated")
    logging.info("Step 7: messages received %s", len(SC.can_messages[can_receive]))
    logging.info("Step 7: messages: %s", SC.can_messages[can_receive])
    logging.info("Step 7: frames received %s", len(SC.can_frames[can_receive]))
    logging.info("Step 7: frames: %s", SC.can_frames[can_receive])
    new_sbl_diagnostic_db_part_number = SC.can_frames[can_receive][0][2].upper()

    # Is it still the same Secondary Bootloader Diagnostic Database Part Number?
    result = sbl_diagnostic_db_part_number == new_sbl_diagnostic_db_part_number
    return result and result


def step_8(stub, can_send, can_receive, can_namespace, result):
    '''
    Step 8: Change to Default session
    '''

    stepno = 8
    purpose = "Change to Default session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send("DiagnosticSessionControl", b'\x01', "")
    can_mr_extra = ''

    return result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send, can_receive,
                                    can_namespace, stepno, purpose, timeout, min_no_messages,
                                    max_no_messages)


def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)
    result = True

    # start logging
    # to be implemented

    # where to connect to signal_broker
    network_stub = SC.connect_to_signalbroker(ODTB_conf.ODTB2_DUT, ODTB_conf.ODTB2_PORT)

    can_send = "Vcu1ToBecmFront1DiagReqFrame"
    can_receive = "BecmToVcu1Front1DiagResFrame"
    can_namespace = SC.nspace_lookup("Front1CANCfg0")

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())

    ############################################
    # precondition
    ############################################
    result = precondition(network_stub, can_send, can_receive, can_namespace, result)

    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: Support function used to activate the secondary Bootloader
    # result: BECM sends positive reply
    result = step_1(network_stub, can_send, can_receive, can_namespace, result)

    # step 2:
    # action: Send 1 requests - requires SF to send, MF for reply.
    #         In our test case we request Complete ECU Part/Serial Number
    # result: BECM sends positive reply
    result = step_2(network_stub, can_send, can_receive, can_namespace, result)

    # step 3:
    # action: Test if DIDs are included in reply. In our test case we request
    #         Complete ECU Part/Serial Number
    # result: BECM sends positive reply
    result, sbl_diagnostic_db_part_number = step_3(can_receive, result)

    # step 4: Verify if number for requests limited in programming session
    # action: Send several requests at one time - requires SF to send, MF for reply
    # result:
    result = step_4(network_stub, can_send, can_receive, can_namespace, result)

    # step 5: Verify if number for requests limited in programming session
    # action: Check if expected DID are contained in reply
    # result: True if all contained, false if not
    result = step_5(can_receive, result)

    # step 6: Verify that we are still on SBL reading out the same SW serial number as in step 3
    # action: Send 1 requests - requires SF to send, MF for reply.
    #         In our test case we request Complete ECU Part/Serial Number
    # result:
    result = step_6(network_stub, can_send, can_receive, can_namespace, result)
    time.sleep(1)

    # step 7:
    # action: Verify that we are still on SBL reading out the same SW serial number as in step 3
    # result: BECM reports mode
    result = step_7(can_receive, result, sbl_diagnostic_db_part_number)
    time.sleep(1)

    # step 8:
    # action: Change to Default session
    # result: BECM reports mode
    result = step_8(network_stub, can_send, can_receive, can_namespace, result)
    time.sleep(1)

    ############################################
    # postCondition
    ############################################

    logging.debug("\nTime: %s \n", time.time())
    logging.info("Testcase end: %s", datetime.now())
    logging.info("Time needed for testrun (seconds): %s", int(time.time() - starttime))

    logging.info("Do cleanup now...")
    logging.info("Stop all periodic signals sent")
    SC.stop_periodic_all()

    # deregister signals
    SC.unsubscribe_signals()
    # if threads should remain: try to stop them
    SC.thread_stop()

    logging.info("Test cleanup end: %s\n", datetime.now())

    if result:
        logging.info("Testcase result: PASSED")
    else:
        logging.info("Testcase result: FAILED")


if __name__ == '__main__':
    run()
