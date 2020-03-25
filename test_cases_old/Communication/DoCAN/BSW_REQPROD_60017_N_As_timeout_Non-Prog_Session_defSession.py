# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   hweiler (Hans-Klaus Weiler)
# date:     2019-05-17
# version:  1.0
# reqprod:  60017

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

    # Parameters for FrameControl FC VCU
    time.sleep(1)
    block_size=0
    separation_time=0
    frame_control_delay = 0 #no wait
    frame_control_flag = 48 #continue send
    frame_control_auto = False
    SC.change_MF_FC(s, block_size, separation_time, frame_control_delay, frame_control_flag, frame_control_auto)

    print()
    step_0(stub, s, r, ns)

    print ("precondition testok:", testresult, "\n")


# teststep 0: Complete ECU Part/Serial Number(s)
def step_0(stub, s, r, ns):
    global testresult

    stepno = 0
    purpose = "Complete ECU Part/Serial Number(s)"
    timeout = 5
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xED\xA0', "")
    can_mr_extra = ''

    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    print(SuTe.PP_CombinedDID_EDA0(SC.can_messages[r][0][2], title=''))


    # teststep 1: verify session
def step_1(stub, s, r, ns):
    global testresult

    stepno = 1
    purpose = "Verify default session"
    timeout = 5
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x01'

    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    time.sleep(1)


# teststep 2: send request with MF reply, frame_control_delay < timeout
def step_2(stub, s, r, ns):
    global testresult

    stepno = 2
    purpose = "send several requests at one time - requires SF to send"
    timeout = 5 # wait for message to arrive, but don't test (-1)
    min_no_messages = -1
    max_no_messages = -1

    # Parameters for FrameControl FC
    block_size=0
    separation_time=0
    frame_control_delay = 950 #wait 950 ms
    frame_control_flag = 48 #continue send
    frame_control_auto = False

    SC.change_MF_FC(s, block_size, separation_time, frame_control_delay, frame_control_flag, frame_control_auto)
    #SC.change_MF_FC(r, block_size, separation_time, frame_control_delay, frame_control_flag, frame_control_auto)

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xDD\x02\xDD\x0A\xDD\x0C\x49\x47', "")
    can_mr_extra = ''

    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)


# teststep 3: test if DIDs are included in reply
def step_3(stub, s, r, ns):
    global testresult

    stepno = 3
    purpose = "test if all requested DIDs are included in reply"
    #timeout = 5
    #min_no_messages = 1
    #max_no_messages = 0
    #

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

    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DD02')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DD0A')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DD0C')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='4947')


# teststep 4: send request with MF reply, frame_control_delay > timeout
def step_4(stub, s, r, ns):
    print ("Step4 start")
    global testresult

    stepno = 4
    purpose = "send several requests at one time - requires SF to send"
    timeout = 5 # wait for message to arrive, but don't test (-1)
    min_no_messages = -1
    max_no_messages = -1

    # Parameters for FrameControl FC
    block_size=0
    separation_time=0
    frame_control_delay = 1010 #wait 1010 ms with reply
    frame_control_flag = 48 #continue send
    frame_control_auto = False


    SC.change_MF_FC(s, block_size, separation_time, frame_control_delay, frame_control_flag, frame_control_auto)
    #SC.change_MF_FC(r, block_size, separation_time, frame_control_delay, frame_control_flag, frame_control_auto)

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xDD\x02\xDD\x0A\xDD\x0C\x49\x47', "")
    can_mr_extra = ''

    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)


# teststep 5: test if DIDs are included in reply
def step_5(stub, s, r, ns):
    global testresult

    stepno = 5
    purpose = "test if all requested DIDs are included in reply"
    #timeout = 5
    #min_no_messages = 1
    #max_no_messages = 0
    #

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
    print ("Step5: frames received ", len(SC.can_frames[r]))
    print ("Step5: frames: ", SC.can_frames[r], "\n")

    print ("verify that no reply received: len(frames_received) == 1 :", len(SC.can_frames[r]) == 0)
    testresult = testresult and (len(SC.can_frames[r]) == 0)


## teststep 6: set back frame_control_delay to default
def step_6(stub, s, r, ns):
    global testresult

    stepno = 6
    purpose = "set back frame_control_delay to default"
    timeout = 5
    min_no_messages = -1
    max_no_messages = -1

    block_size1 = 1
    block_size=0
    separation_time=0
    frame_control_flag =   48 #continue to send
    frame_control_delay =  0
    frame_control_auto = False

    SuTe.print_test_purpose(stepno, purpose)
    #update_can_messages_2(stub, r)
    #print(can_frames, "\n")
    SC.change_MF_FC(r, block_size, separation_time, frame_control_delay, frame_control_flag, frame_control_auto)




def run():
    global testresult

    #start logging
    # to be implemented

    # where to connect to signal_broker
    network_stub = SC.connect_to_signalbroker(ODTB_conf.ODTB2_DUT, ODTB_conf.ODTB2_PORT)

    can_send = "Vcu1ToBecmFront1DiagReqFrame"
    can_receive = "BecmToVcu1Front1DiagResFrame"
    can_namespace = SC.nspace_lookup("Front1CANCfg0")

    # Test PreCondition
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)
    root.info('BEGIN:  %s' % os.path.basename(__file__))


    print ("Testcase start: ", datetime.now())
    starttime = time.time()
    print ("time ", time.time())
    print ()
    ############################################
    # precondition
    ############################################
    precondition(network_stub, can_send, can_receive, can_namespace)

    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: verify session
    # result: default session
    step_1(network_stub, can_send, can_receive, can_namespace)

    # step2:
    # action: send several requests at one time - requires SF to send, MF for reply
    # result: BECM reports programmin session
    step_2(network_stub, can_send, can_receive, can_namespace)

    # step 3: check if DIDs are included in reply including those from combined DID
    # action: check if expected DID are contained in reply
    # result: true if all contained, false if not
    step_3(network_stub, can_send, can_receive, can_namespace)

    # step4:
    # action: check current session
    # result: BECM reports default session
    step_4(network_stub, can_send, can_receive, can_namespace)

    # step 5: check if DIDs are included in reply including those from combined DID
    # action: check if expected DID are contained in reply
    # result: true if all contained, false if not
    step_5(network_stub, can_send, can_receive, can_namespace)


    # step6:
    # action: send 11 requests at one time
    # result:
    #step_6(network_stub, can_send, can_receive, can_namespace)

    # step 7: check if error message received
    # action: check if error message received
    # result: true if error message contained, false if not
    #step_7(network_stub, can_send, can_receive, can_namespace)

    # step8:
    # action: send 10 requests at one time, containing combined DID
    # result:
    #step_8(network_stub, can_send, can_receive, can_namespace)

    # step 9: check if DIDs are included in reply including those from combined DID
    # action: check if expected DID are contained in reply
    # result: true if all contained, false if not
    #step_9(network_stub, can_send, can_receive, can_namespace)

    ############################################
    # postCondition
    ############################################

    print ()
    print ("time ", time.time())
    print ("Testcase end: ", datetime.now())
    print ("Time needed for testrun (seconds): ", int(time.time() - starttime))


    print ("Do cleanup now...")
    print ("Stop heartbeat sent")
    SC.stop_heartbeat()
    #time.sleep(5)

    # deregister signals
    SC.unsubscribe_signals()
    # if threads should remain: try to stop them
    SC.thread_stop()

    print ("Test cleanup end: ", datetime.now())
    print ()
    if testresult:
        print ("Testcase result: PASSED")
    else:
        print ("Testcase result: FAILED")


if __name__ == '__main__':
    run()
