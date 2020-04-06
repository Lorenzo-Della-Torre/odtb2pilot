# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   hweiler (Hans-Klaus Weiler)
# date:     2019-05-09
# version:  1.0
# reqprod:  76170

#inspired by https://grpc.io/docs/tutorials/basic/python.html

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

import logging
from datetime import datetime
import time
import sys
from Py_testenv.support_test_odtb2 import Support_test_ODTB2
from Py_testenv.support_can import Support_CAN
import Py_testenv.ODTB_conf as ODTB_config

SC = Support_CAN()
SUPPORT_TEST = Support_test_ODTB2()


# precondition for test running:
#  BECM has to be kept alive: start heartbeat
def precondition(stub, can_send, can_receive, can_namespace):
    ''' Precondition '''

    # start heartbeat, repeat every 0.8 second
    SC.start_heartbeat(stub, "EcmFront1NMFr", "Front1CANCfg0", b'\x20\x40\x00\xFF\x00\x00\x00\x00',
                       0.8)

    time.sleep(4) #wait for ECU startup

    timeout = 40   #seconds
    SC.subscribe_signal(stub, can_send, can_receive, can_namespace, timeout)
    #record signal we send as well
    SC.subscribe_signal(stub, can_receive, can_send, can_namespace, timeout)

    test_result = step_0(stub, can_send, can_receive, can_namespace)
    logging.info("Precondition testok: %s\n", test_result)
    return test_result


# teststep 0: Complete ECU Part/Serial Number(s)
def step_0(stub, can_send, can_receive, can_namespace):
    ''' Step 0 '''
    stepno = 0
    purpose = "Complete ECU Part/Serial Number(s)"
    timeout = 5
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send("ReadDataByIdentifier", b'\xED\xA0', "")
    can_mr_extra = ''

    test_result = SUPPORT_TEST.teststep(stub, can_m_send, can_mr_extra, can_send,
                                        can_receive, can_namespace, stepno, purpose,
                                        timeout, min_no_messages, max_no_messages)
    logging.info(SUPPORT_TEST.PP_CombinedDID_EDA0(SC.can_messages[can_receive][0][2], title=''))
    return test_result


# teststep 1: send 1 requests - requires SF to send, MF for reply
def step_1(stub, can_send, can_receive, can_namespace): # pylint: disable=too-many-locals
    ''' Step 1 '''

    stepno = 1
    purpose = "send 1 request - requires SF to send"
    timeout = 5 # wait for message to arrive, but don't test (-1)
    min_no_messages = -1
    max_no_messages = -1

    # Parameters for FrameControl FC
    block_size = 0
    separation_time = 0
    frame_control_delay = 0 #no wait
    frame_control_flag = 48 #continue send
    frame_control_auto = False

    can_m_send = SC.can_m_send("ReadDataByIdentifier", b'\xF1\x20', "")
    can_mr_extra = ''

    SC.change_MF_FC(can_send, block_size, separation_time, frame_control_delay, frame_control_flag,
                    frame_control_auto)

    test_result = SUPPORT_TEST.teststep(stub, can_m_send, can_mr_extra, can_send,
                                        can_receive, can_namespace, stepno, purpose,
                                        timeout, min_no_messages, max_no_messages)
    return test_result

# teststep 2: test if DIDs are included in reply
def step_2(can_receive):
    ''' Step 2 '''
    stepno = 2
    purpose = "test if requested DID are included in reply"

    SUPPORT_TEST.print_test_purpose(stepno, purpose)

    time.sleep(1)
    SC.clear_all_can_messages()
    logging.info("All can messages cleared")
    SC.update_can_messages(can_receive)
    logging.info("All can messages updated")
    logging.info("Step2: messages received %s", len(SC.can_messages[can_receive]))
    logging.info("Step2: messages: %s\n", SC.can_messages[can_receive])
    logging.info("Step2: frames received %s", len(SC.can_frames[can_receive]))
    logging.info("Step2: frames: %s\n", SC.can_frames[can_receive])
    logging.info("Test if string contains all IDs expected:")
    test_result = SUPPORT_TEST.test_message(SC.can_messages[can_receive], teststring='F120')
    return test_result


# teststep 3: send several requests at one time - requires SF to send, MF for reply
def step_3(stub, can_send, can_receive, can_namespace): # pylint: disable=too-many-locals
    '''' Step 3 '''
    stepno = 3
    purpose = "send several requests at one time - requires SF to send"
    timeout = 5 # wait for message to arrive, but don't test (-1)
    min_no_messages = -1
    max_no_messages = -1

    # Parameters for FrameControl FC
    block_size = 0
    separation_time = 0
    frame_control_delay = 0 #no wait
    frame_control_flag = 48 #continue send
    frame_control_auto = False

    can_m_send = SC.can_m_send("ReadDataByIdentifier", b'\xF1\x20\xF1\x2A', "")
    can_mr_extra = ''

    SC.change_MF_FC(can_send, block_size, separation_time, frame_control_delay, frame_control_flag,
                    frame_control_auto)

    test_result = SUPPORT_TEST.teststep(stub, can_m_send, can_mr_extra, can_send,
                                        can_receive, can_namespace, stepno, purpose,
                                        timeout, min_no_messages, max_no_messages)
    return test_result

# teststep 4: test if DIDs are included in reply
def step_4(can_receive):
    ''' Step 4 '''
    stepno = 4
    purpose = "test if all requested DIDs are included in reply"

    SUPPORT_TEST.print_test_purpose(stepno, purpose)

    time.sleep(1)
    SC.clear_all_can_messages()
    logging.info("all can messages cleared")
    SC.update_can_messages(can_receive)
    logging.info("all can messages updated")
    logging.info("Step4: messages received %s", len(SC.can_messages[can_receive]))
    logging.info("Step4: messages: %s\n", SC.can_messages[can_receive])
    logging.info("Step4: frames received %s", len(SC.can_frames[can_receive]))
    logging.info("Step4: frames: %s\n", SC.can_frames[can_receive])
    logging.info("Test if string contains all IDs expected:")

    test_result = SUPPORT_TEST.test_message(SC.can_messages[can_receive], teststring='F120')
    test_result = test_result and SUPPORT_TEST.test_message(SC.can_messages[can_receive],
                                                            teststring='F12A')
    return test_result


def main(margs):
    ''' Main '''
    # Setting up logging
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)

    # If we have a config file as input parameter, then use it. Otherwise use default.
    config_file = Support_test_ODTB2.config(margs)
    logging.debug('Config File name: %s', config_file)

    # where to connect to signal_broker
    network_stub = SC.connect_to_signalbroker(ODTB_config.ODTB2_DUT, ODTB_config.ODTB2_PORT)

    can_send = "Vcu1ToBecmFront1DiagReqFrame"
    can_receive = "BecmToVcu1Front1DiagResFrame"
    can_namespace = SC.nspace_lookup("Front1CANCfg0")

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time %s\n", time.time())

    ############################################
    # precondition
    ############################################
    test_result = precondition(network_stub, can_send, can_receive, can_namespace)

    ############################################
    # teststeps
    ############################################

    # step1:
    # action: send 1 request - requires SF to send, MF for reply
    # result: BECM reports default session
    test_result = test_result and step_1(network_stub, can_send, can_receive, can_namespace)

    # step 2: check if DID is included in reply
    # action: check if expected DID are contained in reply
    # result: true if all contained, false if not
    test_result = test_result and step_2(can_receive)

    # step3:
    # action: send several requests at one time - requires SF to send, MF for reply
    # result: BECM reports default session
    test_result = test_result and step_3(network_stub, can_send, can_receive, can_namespace)

    # step 4: check if DIDs are included in reply including those from combined DID
    # action: check if expected DID are contained in reply
    # result: true if all contained, false if not
    test_result = test_result and step_4(can_receive)


    ############################################
    # postCondition
    ############################################

    logging.info("\ntime %s", time.time())
    logging.info("Testcase end: %s", datetime.now())
    logging.info("Time needed for testrun (seconds): %d", int(time.time() - starttime))
    logging.info("Do cleanup now...")
    logging.info("Stop heartbeat sent")
    SC.stop_heartbeat()

    # deregister signals
    SC.unsubscribe_signals()
    # if threads should remain: try to stop them
    SC.thread_stop()

    logging.info("Test cleanup end: %s\n", datetime.now())

    if test_result:
        logging.info("Testcase result: PASSED")
    else:
        logging.info("Testcase result: FAILED")


if __name__ == '__main__':
    # Boilerplate to launch the main function with the command line arguments.
    ARGS = Support_test_ODTB2.parse_some_args()
    main(ARGS)
