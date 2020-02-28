# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO
# date:     2020-01-20
# reqprod:  53843
# version:  1.0

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

import time
from datetime import datetime
import sys
import logging
import argparse

import ODTB_conf
from support_can import Support_CAN
from support_test_odtb2 import Support_test_ODTB2
from support_SecAcc import Support_Security_Access
from support_SBL import Support_SBL

SC = Support_CAN()
SUTE = Support_test_ODTB2()
SSA = Support_Security_Access()
SSBL = Support_SBL()

DB_NUMBER = None

def parse_some_args():
    """Get the command line input, using the defined flags."""
    parser = argparse.ArgumentParser(description='Check format of DID file')
    parser.add_argument("--did_file", help="DID-File", type=str, action='store', dest='did_file', required=False,)
    ret_args = parser.parse_args()
    return ret_args


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
    timeout = 50
    SC.subscribe_signal(stub, can_send, can_receive, can_namespace, timeout)
    #record signal we send as well
    SC.subscribe_signal(stub, can_receive, can_send, can_namespace, timeout)

    #wait for signals to be registered
    time.sleep(1)
    # Change frame_control_auto for signal we’re sending
    block_size = 0
    separation_time = 0
    frame_control_delay = 0 #no wait
    frame_control_flag = 48 #continue send
    frame_control_auto = False

    SC.change_MF_FC(can_send, block_size, separation_time, frame_control_delay, frame_control_flag,
                    frame_control_auto)

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
    """
    Teststep 1: verify RoutineControlRequest is sent for Type 1
    """
    stepno = 1
    purpose = "verify RoutineControl start is sent for Check Programming Preconditions"
    timeout = 1 #wait a second for reply to be send
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send("RoutineControlRequestSID", b'\x02\x06', b'\x01')
    can_mr_extra = ''

    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)

    result = result and SUTE.PP_Decode_Routine_Control_response(SC.can_messages[can_receive][0][2],
                                                                'Type1,Completed')
    return result

def step_2(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 2: Change to Programming session
    """
    stepno = 2
    purpose = "Change to Programming session(01) from default"
    timeout = 1
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send("DiagnosticSessionControl", b'\x02', "")
    can_mr_extra = ''

    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)

    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)
    return result

def step_3(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 3: Security Access Request SID
    """
    stepno = 3
    purpose = "Security Access Request SID"
    result = result and SSA.activation_security_access(stub, can_send, can_receive, can_namespace,
                                                       stepno, purpose)
    return result


def step_4(stub, can_send, can_receive, can_namespace, result):
    '''
    Teststep 4: Extract SWP Number for PBL
    '''
    stepno = 4
    purpose = "Extract SWP Number for PBL"
    timeout = 5 # wait for message to arrive, but don't test (-1)
    min_no_messages = 1
    max_no_messages = 1
    global DB_NUMBER
    # Parameters for FrameControl FC
    block_size = 0
    separation_time = 0
    frame_control_delay = 0 #no wait
    frame_control_flag = 48 #continue send
    frame_control_auto = False

    can_m_send = SC.can_m_send("ReadDataByIdentifier", b'\xF1\x21', "")
    can_mr_extra = ''

    SC.change_MF_FC(can_send, block_size, separation_time, frame_control_delay, frame_control_flag,
                    frame_control_auto)

    result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send, can_receive,
                             can_namespace, stepno, purpose, timeout, min_no_messages,
                             max_no_messages)
    logging.info("Step 4: %s", SUTE.PP_PartNumber(SC.can_messages[can_receive][0][2][10:]))
    DB_NUMBER = SUTE.PP_PartNumber(SC.can_messages[can_receive][0][2][10:])
    return result

def step_5(margs):
    """
    Teststep 1: Extract all DID from Data Base
    """
    stepno = 5
    purpose = "Extract all DID from Data Base"
    SUTE.print_test_purpose(stepno, purpose)
    did_list = SUTE.Extract_DB_DID_ID(DB_NUMBER, margs)
    return did_list

def step_6(stub, can_send, can_receive, can_namespace, did_list, result):
    '''
    Teststep 6: Test if all DIDs in DB are present in SW PBL
    '''
    stepno = 6
    purpose = "Test if all DIDs in DB are present in SW PBL"
    timeout = 1 # wait for message to arrive, but don't test (-1)
    min_no_messages = 1
    max_no_messages = 1

    for did in did_list:
        can_m_send = SC.can_m_send("ReadDataByIdentifier", bytes.fromhex(did), "")
        can_mr_extra = ''

        result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send, can_receive,
                                 can_namespace, stepno, purpose, timeout, min_no_messages,
                                 max_no_messages)
    return result

def step_7(stub, can_send, can_receive, can_namespace, result):
    '''
    Teststep 7: Test if DIDs not in DB return Error message
    '''
    stepno = 7
    purpose = "Test if DIDs not in DB return Error message"
    timeout = 1 # wait for message to arrive, but don't test (-1)
    min_no_messages = -1
    max_no_messages = -1


    can_m_send = SC.can_m_send("ReadDataByIdentifier", b'\xF1\x02', "")
    can_mr_extra = ''

    result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send, can_receive,
                             can_namespace, stepno, purpose, timeout, min_no_messages,
                             max_no_messages)

    result = result and SUTE.test_message(SC.can_messages[can_receive], teststring='7F2231')
    #logging.info('%s', SUTE.PP_Decode_7F_response(SC.can_frames[can_receive][0][2]))
    return result

def step_8(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 8: Reset
    """
    stepno = 8
    purpose = "ECU Reset"
    timeout = 1
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = b'\x11\x01'
    can_mr_extra = ''

    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)

    result = result and SUTE.test_message(SC.can_messages[can_receive], teststring='025101')
    return result

def step_9(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 9: verify session
    """
    stepno = 9
    purpose = "Verify Default session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send("ReadDataByIdentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x01'

    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)
    return result


def run(margs):
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
    # action:
    # result:
    result = step_1(network_stub, can_send, can_receive, can_namespace, result)

    # step 2:
    # action:
    # result:
    result = step_2(network_stub, can_send, can_receive, can_namespace, result)

    # step 3:
    # action:
    # result:
    result = step_3(network_stub, can_send, can_receive, can_namespace, result)

    # step 4:
    # action:
    # result:
    result = step_4(network_stub, can_send, can_receive, can_namespace, result)

    # step 5:
    # action:
    # result:
    did_list = step_5(margs)

    # step 6:
    # action:
    # result:
    result = step_6(network_stub, can_send, can_receive, can_namespace, did_list, result)

    # step 7:
    # action:
    # result:
    result = step_7(network_stub, can_send, can_receive, can_namespace, result)

    # step 8:
    # action:
    # result:
    result = step_8(network_stub, can_send, can_receive, can_namespace, result)
    time.sleep(1)

    # step 9:
    # action:
    # result:
    result = step_9(network_stub, can_send, can_receive, can_namespace, result)
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
    ARGS = parse_some_args()
    run(ARGS)
