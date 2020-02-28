# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   hweiler (Hans-Klaus Weiler)
# date:     2019-05-17
# version:  1.0
# reqprod:  60006

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
    timeout = 1
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x01'

    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)


# teststep 2: send request with MF to send
def step_2(stub, s, r, ns):
    global testresult

    stepno = 2
    purpose = "send several requests at one time - requires MF to send"
    timeout = 1 # wait for message to arrive, but don't test (-1)
    min_no_messages = -1
    max_no_messages = -1

    # Parameters for FrameControl FC
    block_size=0
    separation_time=0
    frame_control_delay = 0 #wait 950 ms
    frame_control_flag = 48 #wait with send
    frame_control_auto = False

    SC.change_MF_FC(s, block_size, separation_time, frame_control_delay, frame_control_flag, frame_control_auto)

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xDD\x02\xDD\x0A\xDD\x0C\x49\x47', "")
    can_mr_extra = ''

    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
# verify FC parameters from BECM for block_size
    print ("FC parameters used:")
    print ("Step2: frames received ", len(SC.can_frames[r]))
    print ("Step2: frames: ", SC.can_frames[r], "\n")
    print ("len FC ", len(SC.can_cf_received[r]))
    print ("FC: ", SC.can_cf_received[r])
    #print ("FC: ", Support_CAN.can_cf_received)
    testresult = SuTe.test_message(SC.can_cf_received[r], teststring='30000A0000000000') and testresult

# teststep 3: test if DIDs are included in reply
def step_3(stub, s, r, ns):
    global testresult

    stepno = 3
    purpose = "test if all requested DIDs are included in reply"
    #timeout = 5
    #min_no_messages = 1
    #max_no_messages = 0
    #

    SuTe.print_test_purpose(stepno, purpose)

    print ()
    print ("Step3: messages received ", len(SC.can_messages[r]))
    print ("Step3: messages: ", SC.can_messages[r], "\n")
    print ("Step3: frames received ", len(SC.can_frames[r]))
    print ("Step3: frames: ", SC.can_frames[r], "\n")
    print ("Test if string contains all IDs expected:")

    testresult = SuTe.test_message(SC.can_messages[r], teststring='DD02') and testresult
    testresult = SuTe.test_message(SC.can_messages[r], teststring='DD0A') and testresult
    testresult = SuTe.test_message(SC.can_messages[r], teststring='DD0C') and testresult
    testresult = SuTe.test_message(SC.can_messages[r], teststring='4947') and testresult
    print()


# teststep 4: build longer message to send
def step_4(stub, s, r, ns):
    global testresult

    stepno = 4
    purpose = "send several requests at one time - requires MF to send"
    timeout = 1 # wait for message to arrive, but don't test (-1)
    min_no_messages = -1
    max_no_messages = -1

    # message to send:
    payload = b'\xDD\x02\xDD\x0A\xDD\x0C\x49\x47'

    #pl_max_length = 4090
    pl_max_length = 12
    while len(payload) < pl_max_length:
        payload = payload + b'\x00'

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", payload, "")
    can_mr_extra = ''

    testresult = SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages) and testresult
# verify FC parameters from BECM for block_size
    print ("FC parameters used:")
    print ("Step4: frames received ", len(SC.can_frames[r]))
    print ("Step4: frames: ", SC.can_frames[r], "\n")
    print ("len FC ", len(SC.can_cf_received[r]))
    print ("FC: ", SC.can_cf_received[r])
    #print ("FC: ", Support_CAN.can_cf_received)

# teststep 5: test if DIDs are included in reply
def step_5(stub, s, r, ns):
    global testresult

    stepno = 5
    purpose = "test if all requested DIDs are included in reply"

    SuTe.print_test_purpose(stepno, purpose)


    #time.sleep(1)
    #SC.clear_all_can_messages()
    #print ("all can messages cleared")
    #SC.update_can_messages(r)
    #print ("all can messages updated")
    print ()
    print ("Step5: messages received ", len(SC.can_messages[r]))
    print ("Step5: messages: ", SC.can_messages[r], "\n")
    print ("Step5: frames received ", len(SC.can_frames[r]))
    print ("Step5: frames: ", SC.can_frames[r], "\n")
    print ("Test if string contains all IDs expected:")

    testresult = SuTe.test_message(SC.can_messages[r], teststring='DD02') and testresult
    testresult = SuTe.test_message(SC.can_messages[r], teststring='DD0A') and testresult
    testresult = SuTe.test_message(SC.can_messages[r], teststring='DD0C') and testresult
    testresult = SuTe.test_message(SC.can_messages[r], teststring='4947') and testresult
    print()

# teststep 6: build longer message to send
def step_6(stub, s, r, ns):
    global testresult

    stepno = 6
    purpose = "send several requests at one time - requires MF to send"
    timeout = 1 # wait for message to arrive, but don't test (-1)
    min_no_messages = -1
    max_no_messages = -1

    # message to send:
    payload = b'\xDD\x02\xDD\x0A\xDD\x0C\x49\x47'

    #pl_max_length = 4090
    #pl_max_length = 252
    pl_max_length = 251
    #pl_max_length = 51
    while len(payload) < pl_max_length:
        payload = payload + b'\x00'

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", payload, "")
    can_mr_extra = ''

    testresult = SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages) and testresult
# verify FC parameters from BECM for block_size
    print ("FC parameters used:")
    print ("Step6: frames received ", len(SC.can_frames[r]))
    print ("Step6: frames: ", SC.can_frames[r], "\n")
    print ("len FC ", len(SC.can_cf_received[r]))
    print ("FC: ", SC.can_cf_received[r])
    #print ("FC: ", Support_CAN.can_cf_received)

# teststep 7: test if DIDs are included in reply
def step_7(stub, s, r, ns):
    global testresult

    stepno = 7
    purpose = "test if all requested DIDs are included in reply"

    SuTe.print_test_purpose(stepno, purpose)

    #time.sleep(1)
    #SC.clear_all_can_messages()
    #print ("all can messages cleared")
    #SC.update_can_messages(r)
    #print ("all can messages updated")
    print ()
    print ("Step7: messages received ", len(SC.can_messages[r]))
    print ("Step7: messages: ", SC.can_messages[r], "\n")
    print ("Step7: frames received ", len(SC.can_frames[r]))
    print ("Step7: frames: ", SC.can_frames[r], "\n")
    print ("Test if string contains all IDs expected:")

    #testresult = SuTe.test_message(SC.can_messages[r], teststring='DD02') and testresult
    #testresult = SuTe.test_message(SC.can_messages[r], teststring='DD0A') and testresult
    #testresult = SuTe.test_message(SC.can_messages[r], teststring='DD0C') and testresult
    #testresult = SuTe.test_message(SC.can_messages[r], teststring='4947') and testresult
    #print()

    testresult = testresult and (SuTe.test_message(SC.can_messages[r], teststring='7F2231') or SuTe.test_message(SC.can_messages[r], teststring='7F2213'))
    print ("Error  message: ")
    print ("SC.can_messages[r]",SC.can_messages[r][0][2])
    print (SuTe.PP_Decode_7F_response(SC.can_messages[r][0][2]))
    print ("Step ", stepno, " teststatus:", testresult, "\n")

# teststep 8: build payload >255 bytes
def step_8(stub, s, r, ns):
    global testresult

    stepno = 8
    purpose = "send several requests at one time - requires MF to send"
    timeout = 1 # wait for message to arrive, but don't test (-1)
    min_no_messages = -1
    max_no_messages = -1

    # Parameters for FrameControl FC
    #block_size=0
    #separation_time=0
    #frame_control_delay = 0 #wait 950 ms
    #frame_control_flag = 48 #wait with send
    #frame_control_auto = False
    #
    #SC.change_MF_FC(s, block_size, separation_time, frame_control_delay, frame_control_flag, frame_control_auto)

    # message to send:
    payload = b'\xDD\x02\xDD\x0A\xDD\x0C\x49\x47'

    #pl_max_length = 1090
    pl_max_length = 256
    #pl_max_length = 400
    while len(payload) < pl_max_length:
        payload = payload + b'\x00'

    print ("send  mmessage with 4090 bytes")
    print ("message: ", payload)
    can_m_send = SC.can_m_send( "ReadDataByIdentifier", payload, "")
    can_mr_extra = ''

    #testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    testresult = SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages) and testresult

    # verify FC parameters from BECM for block_size
    print ()
    print ("Step8: frames received ", len(SC.can_frames[r]))
    print ("Step8: frames: ", SC.can_frames[r], "\n")
    print ("len FC ", len(SC.can_cf_received[r]))
    print ("FC: ", SC.can_cf_received[r])
    #print ("FC: ", Support_CAN.can_cf_received)

# teststep 9: test if DIDs are included in reply
def step_9(stub, s, r, ns):
    global testresult

    stepno = 9
    purpose = "test if all requested DIDs are included in reply"
    #timeout = 5
    #min_no_messages = 1
    #max_no_messages = 0
    #

    # No normal teststep done,
    # instead: update CAN messages, verify all serial-numbers received (by checking ID for each serial-number)
    #teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)

    SuTe.print_test_purpose(stepno, purpose)

    #time.sleep(1)
    #SC.clear_all_can_messages()
    #print ("all can messages cleared")
    #SC.update_can_messages(r)
    #print ("all can messages updated")
    print ()
    print ("Step9: messages received ", len(SC.can_messages[r]))
    print ("Step9: messages: ", SC.can_messages[r], "\n")
    print ("Step9: frames received ", len(SC.can_frames[r]))
    print ("Step9: frames: ", SC.can_frames[r], "\n")
    print ("Test if string contains all IDs expected:")

    #testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DD02')
    #testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DD0A')
    #testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DD0C')
    #testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='4947')
    testresult = SuTe.test_message(SC.can_frames[r], teststring='32000A') and testresult
    print()

    #print ("Error  message: ")
    #print ("SC.can_messages[r]",SC.can_messages[r][0][2])
    #print (SuTe.PP_Decode_7F_response(SC.can_messages[r][0][2]))
    #print ("Step ", stepno, " teststatus:", testresult, "\n")

# teststep 10: verify session
def step_10(stub, s, r, ns):
    global testresult

    stepno = 10
    purpose = "Verify Default session"
    timeout = 5
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x01'

    testresult = SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages) and testresult
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

    # Test PreCondition
    #root = logging.getLogger()
    #root.setLevel(logging.DEBUG)
    #
    #ch = logging.StreamHandler(sys.stdout)
    #ch.setLevel(logging.DEBUG)
    #formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    #ch.setFormatter(formatter)
    #root.addHandler(ch)
    #root.info('BEGIN:  %s' % os.path.basename(__file__))


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
    # step 1:
    # action: change BECM to programming
    # result: BECM reports mode
    step_1(network_stub, can_send, can_receive, can_namespace)

    # step2:
    # action: check current session
    # result: BECM reports programmin session
    step_2(network_stub, can_send, can_receive, can_namespace)

    # step3:
    # action: send 'hard_reset' to BECM
    # result: BECM acknowledges message
    #step_3(network_stub, can_send, can_receive, can_namespace)

    # step4:
    # action: check current session
    # result: BECM reports default session

    #step_3(network_stub, can_send, can_receive, can_namespace)

    #step_4(network_stub, can_send, can_receive, can_namespace)

    #step_5(network_stub, can_send, can_receive, can_namespace)

    step_3(network_stub, can_send, can_receive, can_namespace)

    step_4(network_stub, can_send, can_receive, can_namespace)

    step_5(network_stub, can_send, can_receive, can_namespace)

    step_6(network_stub, can_send, can_receive, can_namespace)

    step_7(network_stub, can_send, can_receive, can_namespace)

    step_8(network_stub, can_send, can_receive, can_namespace)

    step_9(network_stub, can_send, can_receive, can_namespace)

    step_10(network_stub, can_send, can_receive, can_namespace)

    #step_11(network_stub, can_send, can_receive, can_namespace)

    #step_12(network_stub, can_send, can_receive, can_namespace)

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
    #time.sleep(5)

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