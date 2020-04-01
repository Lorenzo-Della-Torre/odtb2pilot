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

    time.sleep(4) #wait for ECU startup

    timeout = 40   #seconds
    SC.subscribe_signal(stub, s, r, ns, timeout)
    #record signal we send as well
    SC.subscribe_signal(stub, r, s, ns, timeout)

    print()
    step_0(stub, s, r, ns)

    print ("precondition testok:", testresult, "\n")


# teststep 0: Complete ECU Part/Serial Number(s)
def step_0(stub, s, r, ns):
    global testresult

    stepno = 0
    purpose = "Complete ECU Part/Serial Number(s)"
    timeout = 5
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xED\xA0', "")
    can_mr_extra = ''

    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    print(SuTe.PP_CombinedDID_EDA0(SC.can_messages[r][0][2], title=''))

    # teststep 1: Change to Programming session
def step_1(stub, s, r, ns):
    global testresult

    stepno = 1
    purpose = "Change to Programming session"
    timeout = 1
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "DiagnosticSessionControl", b'\x02', "")
    can_mr_extra = ''

    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)

    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)

    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='5002')


# teststep 2: send 1 requests - requires SF to send, MF for reply
def step_2(stub, s, r, ns):
    global testresult

    stepno = 2
    purpose = "send 1 request - requires SF to send"
    timeout = 1 # wait for message to arrive, but don't test (-1)
    min_no_messages = -1
    max_no_messages = -1

    # Parameters for FrameControl FC
    block_size=0
    separation_time=0
    frame_control_delay = 0 #no wait
    frame_control_flag = 48 #continue send
    frame_control_auto = False

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x21', "")
    can_mr_extra = ''

    SC.change_MF_FC(s, block_size, separation_time, frame_control_delay, frame_control_flag, frame_control_auto)

    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)

# teststep 3: test if DIDs are included in reply
def step_3(stub, s, r, ns):
    global testresult

    stepno = 3
    purpose = "test if requested DID are included in reply"

    # No normal teststep done,
    # instead: update CAN messages, verify all serial-numbers received (by checking ID for each serial-number)
    #teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)

    SuTe.print_test_purpose(stepno, purpose)

    time.sleep(1)
    SC.clear_all_can_messages()
    print ("all can messages cleared")
    SC.update_can_messages(r)
    print ("all can messages updated")
    print ()
    print ("Step3: messages received ", len(SC.can_messages[r]))
    print ("Step3: messages: ", SC.can_messages[r], "\n")
    print ("Step3: frames received ", len(SC.can_frames[r]))
    print ("Step3: frames: ", SC.can_frames[r], "\n")
    print ("Test if string contains all IDs expected:")

    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F121')


# teststep 4: send several requests at one time - requires SF to send, MF for reply
def step_4(stub, s, r, ns):
    global testresult

    stepno = 4
    purpose = "send several requests at one time - requires SF to send"
    timeout = 1 # wait for message to arrive, but don't test (-1)
    min_no_messages = -1
    max_no_messages = -1

    # Parameters for FrameControl FC
    block_size=0
    separation_time=0
    frame_control_delay = 0 #no wait
    frame_control_flag = 48 #continue send
    frame_control_auto = False

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x21\xF1\x2A', "")
    can_mr_extra = ''

    SC.change_MF_FC(s, block_size, separation_time, frame_control_delay, frame_control_flag, frame_control_auto)

    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)

# teststep 5: Verify if number for requests limited in programming session
def step_5(stub, s, r, ns):
    global testresult
    #
    stepno = 5
    purpose = "Verify if number for requests limited in programming session"

    # No normal teststep done,
    # instead: update CAN messages, verify all serial-numbers received (by checking ID for each serial-number)
    #teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)

    SuTe.print_test_purpose(stepno, purpose)

    time.sleep(1)
    SC.clear_all_can_messages()
    print ("all can messages cleared")
    SC.update_can_messages(r)
    print ("all can messages updated")
    print ()
    print ("Step5: messages received ", len(SC.can_messages[r]))
    print ("Step5: messages: ", SC.can_messages[r], "\n")
    print ("Step5: frames received ", len(SC.can_frames[r]))
    print ("Step5: frames: ", SC.can_frames[r], "\n")
    print ("Test if string contains all IDs expected:")

    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='037F223100000000')
    print(SuTe.PP_Decode_7F_response(SC.can_frames[r][0][2]))

    # teststep 6: verify session
def step_6(stub, s, r, ns):
    global testresult

    stepno = 6
    purpose = "Verify Programming session"
    timeout = 1
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x02'

    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    time.sleep(1)

    # teststep 7: Change to Default session
def step_7(stub, s, r, ns):
    global testresult

    stepno = 7
    purpose = "Change to Default session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "DiagnosticSessionControl", b'\x01', "")
    can_mr_extra = ''

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

    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: # Change to Extended session
    # result: BECM reports mode
    step_1(network_stub, can_send, can_receive, can_namespace)

    # step2:
    # action: send 1 request - requires SF to send, MF for reply
    # result: BECM reports default session
    step_2(network_stub, can_send, can_receive, can_namespace)

    # step 3: check if DID is included in reply
    # action: check if expected DID are contained in reply
    # result: true if all contained, false if not
    step_3(network_stub, can_send, can_receive, can_namespace)

    # step4:
    # action: send several requests at one time - requires SF to send, MF for reply
    # result: BECM reports default session
    step_4(network_stub, can_send, can_receive, can_namespace)

    # step 5: check if DIDs are included in reply including those from combined DID
    # action: check if expected DID are contained in reply
    # result: true if all contained, false if not
    step_5(network_stub, can_send, can_receive, can_namespace)

    # step6:
    # action: verify current session
    # result: BECM reports programming session
    step_6(network_stub, can_send, can_receive, can_namespace)

    # step 7:
    # action: # Change to Default session
    # result: BECM reports mode
    step_7(network_stub, can_send, can_receive, can_namespace)

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