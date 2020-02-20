# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-09-20
# version:  1.1
# reqprod:  74147

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

import ODTB_conf
from support_can import Support_CAN
from support_test_odtb2 import Support_test_ODTB2

SC = Support_CAN()
SUTE = Support_test_ODTB2()

P4_server_max = 200 # milliseconds
jitter_testenv = 10

def precondition(stub, can_send, can_receive, can_namespace, result):
    """
    Precondition for test running:
    BECM has to be kept alive: start heartbeat
    """

    # start heartbeat, repeat every 0.8 second
    SC.start_heartbeat(stub, "EcmFront1NMFr", "Front1CANCfg0",
                       b'\x20\x40\x00\xFF\x00\x00\x00\x00', 0.8)

    timeout = 40   #seconds
    SC.subscribe_signal(stub, can_send, can_receive, can_namespace, timeout)
    #record signal we send as well
    SC.subscribe_signal(stub, can_receive, can_send, can_namespace, timeout)

    print()
    result = step_0(stub, can_send, can_receive, can_namespace, result)

    print("precondition testok:", result, "\n")
    return result

def step_0(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 0: Complete ECU Part/Serial Number(s)
    """

    stepno = 0
    purpose = "Complete ECU Part/Serial Number(s)"
    timeout = 5
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send("ReadDataByIdentifier", b'\xED\xA0', "")
    can_mr_extra = ''

    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)
    print(SUTE.PP_CombinedDID_EDA0(SC.can_messages[can_receive][0][2], title=''))
    return result

def step_1(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 1: verify ReadDataByIdentifier reply positively
    """
    #global T1, T2
    #global P4_server_max
    stepno = 1
    purpose = "verify ReadDataByIdentifier reply positively"
    timeout = 1 #wait a second for reply to be send
    min_no_messages = 1
    max_no_messages = 1

    #P4_server_max = 200 # seconds
    can_m_send = SC.can_m_send("ReadDataByIdentifier", b'\xF1\x20', "")
    can_mr_extra = ''

    #T1 = time.time()

    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)

    #T2 = SC.can_messages[can_receive][0][0]
    return result

def step_2(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 2: Verify (time receive message – time sending request) < P4_server_max
    """
    stepno = 2
    purpose = "Verify (time receive message – time sending request) less than P4_server_max"
    SUTE.print_test_purpose(stepno, purpose)

    if (int(SC.can_frames[can_send][-1][2][0:1]) == 3) :
        print ("Remove FC frame")
        SC.can_frames[can_send].pop(-1)
    print("Last Can_frame sent:     ", SC.can_frames[can_send][-1])
    print("First CAN_frame received ", SC.can_frames[can_receive][0])

    T_rec = 1000 * SC.can_frames[can_send][-1][0]
    T_send = 1000 * SC.can_frames[can_receive][0][0]

    print ("Time P4_s_max + jitter ", P4_server_max + jitter_testenv)
    print ("Tdiff: T_send-T_rec  : ", (T_send-T_rec))
    #print("T difference(s):", (P4_server_max + 10) - (T_send - T_rec))
    print("Step ", stepno, " teststatus:", result, "\n")

    if (T_rec - T_send) > ((P4_server_max + jitter_testenv)/1000) :
        result = False

    return result

def step_3(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 3: Complete ECU Part/Serial Number(s)
    """
    #global T3, T4
    stepno = 3
    purpose = "Complete ECU Part/Serial Number(s)"
    timeout = 5

    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send("ReadDataByIdentifier", b'\xED\xA0', "")
    can_mr_extra = ''

    #T3 = time.time()

    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)

    #T4 = SC.can_messages[can_receive][0][0]
    return result

def step_4(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 4: Verify (time receive message – time sending request) < P4_server_max
    """
    stepno = 4
    purpose = "Verify (time receive message – time sending request) less than P4_server_max"
    SUTE.print_test_purpose(stepno, purpose)

    if (int(SC.can_frames[can_send][-1][2][0:1]) == 3) :
        print ("Remove FC frame")
        SC.can_frames[can_send].pop(-1)
    print("Last Can_frame sent:     ", SC.can_frames[can_send][-1])
    print("First CAN_frame received ", SC.can_frames[can_receive][0])

    T_rec = 1000 * SC.can_frames[can_send][-1][0]
    T_send = 1000 * SC.can_frames[can_receive][0][0]

    print ("Time P4_s_max + jitter ", P4_server_max + jitter_testenv)
    print ("Tdiff: T_send-T_rec  : ", (T_send-T_rec))
    print("Step ", stepno, " teststatus:", result, "\n")

    if (T_rec - T_send) > ((P4_server_max + jitter_testenv)/1000) :
        result = False

    return result

def step_5(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 5: request 10 DID in one request - those with shortest reply
    """
    #global T5, T6
    stepno = 5
    purpose = "request 10 DID in one request - those with shortest reply (MF send, MF reply)"
    timeout = 5 # wait for message to arrive, but don't test (-1)
    min_no_messages = -1
    max_no_messages = -1

    # Parameters for FrameControl FC
    block_size=0
    ST=0
    FC_delay = 0 #no wait
    FC_flag = 48 #continue send
    FC_auto = False
    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xDD\x02\xDD\x0A\xDD\x0C\x49\x47\x49\x50\xDA\xD0\xDA\xD1\x48\x02\x48\x03\x49\x45', "")
    can_mr_extra = ''

    SC.change_MF_FC(can_send, block_size, ST, FC_delay, FC_flag, FC_auto)

    #T5 = time.time()

    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)

    #T6 = SC.can_messages[can_receive][0][0]
    return result


def step_6(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 6: Verify (time receive message – time sending request) < P4_server_max
    """
    stepno = 6
    purpose = "Verify (time receive message – time sending request) less than P4_server_max"
    SUTE.print_test_purpose(stepno, purpose)

    if (int(SC.can_frames[can_send][-1][2][0:1]) == 3) :
        print ("Remove FC frame")
        SC.can_frames[can_send].pop(-1)
    print("Last Can_frame sent:     ", SC.can_frames[can_send][-1])
    print("First CAN_frame received ", SC.can_frames[can_receive][0])

    T_rec = 1000 * SC.can_frames[can_send][-1][0]
    T_send = 1000 * SC.can_frames[can_receive][0][0]

    print ("Time P4_s_max + jitter ", P4_server_max + jitter_testenv)
    print ("Tdiff: T_send-T_rec  : ", (T_send-T_rec))
    print("Step ", stepno, " teststatus:", result, "\n")

    if (T_rec - T_send) > ((P4_server_max + jitter_testenv)/1000) :
        result = False

    return result


def run():
    """
    Run
    """

    test_result = True

    # start logging
    # to be implemented

    # where to connect to signal_broker
    network_stub = SC.connect_to_signalbroker(ODTB_conf.ODTB2_DUT, ODTB_conf.ODTB2_PORT)

    can_send = "Vcu1ToBecmFront1DiagReqFrame"
    can_receive = "BecmToVcu1Front1DiagResFrame"
    can_namespace = SC.nspace_lookup("Front1CANCfg0")

    print("Testcase start: ", datetime.now())
    starttime = time.time()
    print("time ", time.time())
    print()
    ############################################
    # precondition
    ############################################
    test_result = precondition(network_stub, can_send, can_receive, can_namespace,test_result)

    ############################################
    # teststeps
    ############################################

    # step1:
    # action: send ReadDataByIdentifier signal in default mode
    # result: BECM sends positive reply
    test_result = step_1(network_stub, can_send, can_receive, can_namespace, test_result)

    # step 2:
    # action: Verify (time receive message – time sending request) < P4_server_max
    # result: positive result
    test_result = step_2(network_stub, can_send, can_receive, can_namespace, test_result)

    # step3:
    # action: send ReadDataByIdentifier ED A0
    # result: BECM sends positive reply
    test_result = step_3(network_stub, can_send, can_receive, can_namespace, test_result)

    # step 4:
    # action: Verify (time receive message – time sending request) < P4_server_max
    # result: positive result
    test_result = step_4(network_stub, can_send, can_receive, can_namespace, test_result)

    # step5:
    # action: send ReadDataByIdentifier 10 DID
    # result: BECM sends positive reply
    test_result = step_5(network_stub, can_send, can_receive, can_namespace, test_result)

    # step 6:
    # action: Verify (time receive message – time sending request) < P4_server_max
    # result: positive result
    test_result = step_6(network_stub, can_send, can_receive, can_namespace, test_result)

    ############################################
    # postCondition
    ############################################

    print()
    print("time ", time.time())
    print("Testcase end: ", datetime.now())
    print("Time needed for testrun (seconds): ", int(time.time() - starttime))

    print("Do cleanup now...")
    print("Stop heartbeat sent")
    SC.stop_heartbeat()
    #time.sleep(5)
    # deregister signals
    SC.unsubscribe_signals()
    # if threads should remain: try to stop them
    SC.thread_stop()

    print("Test cleanup end: ", datetime.now())
    print()
    if test_result:
        print("Testcase result: PASSED")
    else:
        print("Testcase result: FAILED")


if __name__ == '__main__':
    run()
