# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   hweiler (Hans-Klaus Weiler)
# date:     2019-05-17
# version:  1.0
# reqprod:  60019

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

from datetime import datetime
import time
import logging
import os
import sys

import ODTB_conf

from support_can import Support_CAN
SC = Support_CAN()

from support_test_odtb2 import Support_test_ODTB2
SuTe = Support_test_ODTB2()

# Global variable:
testresult = True



# precondition for test running:
#  BECM has to be kept alive: start heartbeat
def precondition(stub, s, r, ns):
    global testresult

    # start heartbeat, repeat every 0.8 second
    SC.start_heartbeat(stub, "EcmFront1NMFr", "Front1CANCfg0", b'\x20\x40\x00\xFF\x00\x00\x00\x00', 0.8)

    # timeout = more than maxtime script takes
    # needed as thread for registered signals won't stop without timeout
    #timeout = 300   #seconds
    timeout = 60   #seconds
    SC.subscribe_signal(stub, s, r, ns, timeout)
    #record signal we send as well
    SC.subscribe_signal(stub, r, s, ns, timeout)

    print()
    step_0(stub, s, r, ns)

    print ("precondition testok:", testresult, "\n")


# teststep 0: Complete ECU Part/Serial Number(s)
def step_0(stub, s, r, ns):
    global testresult
    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xED\xA0', "")
    #can_mr_extra = b'\x01'
    can_mr_extra = ''

    stepno = 0
    purpose = "Complete ECU Part/Serial Number(s)"
    timeout = 5
    min_no_messages = 1
    max_no_messages = 1

    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    print(SuTe.PP_CombinedDID_EDA0(SC.can_messages[r][0][2], title=''))

# teststep 1: verify session
def step_1(stub, s, r, ns):
    global testresult

    stepno = 1
    purpose = "Verify default session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x01'

    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)

# teststep 2: request EDA0 - with FC delay < timeout 1000 ms
def step_2(stub, s, r, ns):
    global testresult

    stepno = 2
    purpose = "request EDA0 - with FC delay < timeout 1000 ms"
    timeout = 5
    min_no_messages = -1
    max_no_messages = -1

    block_size1 = 11
    block_size=0
    separation_time=0
    frame_control_flag =   48 #continue to send
    frame_control_delay = 950 #wait 800ms before sending FC frame back
    frame_control_auto = True

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xED\xA0', "")
    can_mr_extra = ''

    #clear_all_can_frames()
    SC.change_MF_FC(r, block_size, separation_time, frame_control_delay, frame_control_flag, frame_control_auto)
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)

    if len(SC.can_frames[r]) == block_size1:
        print ("Timeout due to FC delay: ")
        print ("number of frames received as expected: ", len(SC.can_frames[r]))
    else:
        testresult = False
        print("FAIL: Wrong number of frames received. Expeced", block_size1, "Received:", len(SC.can_frames[r]))
    print ("Step3: frames received ", len(SC.can_frames[r]), "\n")

# teststep 3: request EDA0 - with FC delay > timeout 1000 ms
def step_3(stub, s, r, ns):
    global testresult

    stepno = 3
    purpose = "request EDA0 - with FC delay > timeout 1000 ms"
    timeout = 5
    min_no_messages = -1
    max_no_messages = -1

    block_size1 = 1
    block_size=0
    separation_time=0
    frame_control_flag =   48 #continue to send
    frame_control_delay = 1050 #wait 800ms before sending FC frame back
    frame_control_auto = True

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xED\xA0', "")
    can_mr_extra = ''

    #clear_all_can_frames()
    SC.change_MF_FC(r, block_size, separation_time, frame_control_delay, frame_control_flag, frame_control_auto)
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)

    if len(SC.can_frames[r]) == block_size1:
        print ("Timeout due to FC delay: ")
        print ("number of frames received as expected: ", len(SC.can_frames[r]))
    else:
        testresult = False
        print("FAIL: Wrong number of frames received. Expeced", block_size1, "Received:", len(SC.can_frames[r]))
    print ("Step4: frames received ", len(SC.can_frames[r]), "\n")


# teststep 4: set back frame_control_delay to default
def step_4(stub, s, r, ns):
    global testresult

    stepno = 4
    purpose = "set back frame_control_delay to default"
    timeout = 5
    min_no_messages = -1
    max_no_messages = -1

    block_size1 = 1
    block_size=0
    separation_time=0
    frame_control_flag =   48 #continue to send
    frame_control_delay =  0
    frame_control_auto = True

    SuTe.print_test_purpose(stepno, purpose)
    #update_can_messages_2(stub, r)
    #print(can_frames, "\n")
    SC.change_MF_FC(r, block_size, separation_time, frame_control_delay, frame_control_flag, frame_control_auto)



    # teststep 5: verify session
def step_5(stub, s, r, ns):
    global testresult

    stepno = 5
    purpose = "Verify Default session"
    timeout = 5
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x01'

    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    time.sleep(1)

def run():
    global testresult

    #start logging
    # to be implemented

    # where to connect to signal_broker
    network_stub = SC.connect_to_signalbroker(ODTB_conf.ODTB2_DUT, ODTB_conf.ODTB2_PORT)

    can_send = "Vcu1ToBecmFront1DiagReqFrame"
    can_receive = "BecmToVcu1Front1DiagResFrame"
    can_namespace = SC.nspace_lookup("Front1CANCfg0")

    print ("Testcase start: ", datetime.now())
    starttime = time.time()
    print ("time ", time.time())
    print()
    ############################################
    # precondition
    ############################################
    precondition(network_stub, can_send, can_receive, can_namespace)
    #print ("after precond active threads ", threading.active_count())
    #print ("after precond thread enumerate ", threading.enumerate())

    #subscribe_to_BecmFront1NMFr(network_stub)

    ############################################
    # teststeps
    ############################################
    # step1:
    # action: check current session
    # result: BECM reports programmin session
    step_1(network_stub, can_send, can_receive, can_namespace)

    # step2:
    # action: send request with frame_control_delay < timeout
    # result: whole message received
    step_2(network_stub, can_send, can_receive, can_namespace)

    # step3:
    # action: send request with frame_control_delay > timeout
    # result: only first frame received
    step_3(network_stub, can_send, can_receive, can_namespace)

    # step4:
    # action: restore frame_control_delay again
    # result:
    step_4(network_stub, can_send, can_receive, can_namespace)

    # step5:
    # action: check current session
    # result: BECM reports default session
    step_5(network_stub, can_send, can_receive, can_namespace)


    ############################################
    # postCondition
    ############################################

    print()
    print ("time ", time.time())
    print ("Testcase end: ", datetime.now())
    print ("Time needed for testrun (seconds): ", int(time.time() - starttime))

    print ("Do cleanup now...")
    print ("Stop heartbeat sent")
    SC.stop_heartbeat()

    # deregister signals
    SC.unsubscribe_signals()
    # if threads should remain: try to stop them
    SC.thread_stop()

    print ("Test cleanup end: ", datetime.now())
    print()
    if testresult:
        print ("Testcase result: PASSED")
    else:
        print ("Testcase result: FAILED")


if __name__ == '__main__':
    run()