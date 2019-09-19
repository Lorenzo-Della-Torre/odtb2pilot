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
    

# teststep 1: Change to extended session
def step_1(stub, s, r, ns):
    global testresult
    
    stepno = 1
    purpose = "Change to Extended session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "DiagnosticSessionControl", b'\x03', "")
    can_mr_extra = ''
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    
# teststep 2: send several requests at one time - requires SF to send, MF for reply
def step_2(stub, s, r, ns):
    global testresult
    
    stepno = 2
    purpose = "send several requests at one time - requires SF to send"
    timeout = 1 # wait for message to arrive, but don't test (-1)
    min_no_messages = -1
    max_no_messages = -1

    # Parameters for FrameControl FC
    BS=0
    ST=0
    FC_delay = 0 #no wait
    FC_flag = 48 #continue send
    FC_auto = False
    
    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x20\xF1\x2A', "")
    can_mr_extra = ''
    
    SC.change_MF_FC(s, BS, ST, FC_delay, FC_flag, FC_auto)
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)

# teststep 3: test if DIDs are included in reply
def step_3(stub, s, r, ns):
    global testresult
    
    stepno = 3
    purpose = "test if all requested DIDs are included in reply"

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

    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F120')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F12A')
    
# teststep 4: request 10 DID in one request - those with shortest reply
def step_4(stub, s, r, ns):
    global testresult
    
    stepno = 4
    purpose = "request 10 DID in one request - those with shortest reply (MF send, MF reply)"
    timeout = 1 # wait for message to arrive, but don't test (-1)
    min_no_messages = -1
    max_no_messages = -1

    # Parameters for FrameControl FC
    BS=0
    ST=0
    FC_delay = 0 #no wait
    FC_flag = 48 #continue send
    FC_auto = False
    
    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xDD\x02\xDD\x0A\xDD\x0C\x49\x47\x49\x50\xDA\xD0\xDA\xD1\x48\x02\x48\x03\x49\x45', "")
    can_mr_extra = ''
    
    SC.change_MF_FC(s, BS, ST, FC_delay, FC_flag, FC_auto)
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)


# teststep 5: test if DIDs are included in reply
def step_5(stub, s, r, ns):
    global testresult
    
    stepno = 5
    purpose = "test if all requested DIDs are included in reply"
    
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

    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DD02')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DD0A')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DD0C')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='4947')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='4950')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DAD0')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DAD1')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='4802')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='4803')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='4945')

# teststep 6: request 11 DID at once
def step_6(stub, s, r, ns):
    global testresult
    
    stepno = 6
    purpose = "send 11 requests at one time - fails in current version (max10)"
    timeout = 1 # wait for message to arrive, but don't test (-1)
    min_no_messages = -1
    max_no_messages = -1

    # Parameters for FrameControl FC
    BS=0
    ST=0
    FC_delay = 0 #no wait
    FC_flag = 48 #continue send
    FC_auto = False
    
    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\x49\x1A\xDD\x02\xDD\x0A\xDD\x0C\x49\x47\x49\x50\xDA\xD0\xDA\xD1\x48\x02\x48\x03\x49\x45', "")
    can_mr_extra = ''
    
    SC.change_MF_FC(s, BS, ST, FC_delay, FC_flag, FC_auto)
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)


# teststep 7: test if error received
def step_7(stub, s, r, ns):
    global testresult
    #
    stepno = 7
    purpose = "verify that error message received"
    
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
    print ("Step7: messages received ", len(SC.can_messages[r]))
    print ("Step7: messages: ", SC.can_messages[r], "\n")
    print ("Step7: frames received ", len(SC.can_frames[r]))
    print ("Step7: frames: ", SC.can_frames[r], "\n")
    print ("Test if string contains all IDs expected:")

    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='037F223100000000')
    print ("Error  message: ")
    print ("SC.can_messages[r]",SC.can_messages[r][0][2]) 
    print (SuTe.PP_Decode_7F_response(SC.can_messages[r][0][2]))
    print ("Step ", stepno, " teststatus:", testresult, "\n")

    
# teststep 8: send 10 requests at one time - those with most bytes in return
def step_8(stub, s, r, ns):
    global testresult
    
    stepno = 8
    purpose = "send 10 requests at one time - those with most bytes in return"
    timeout = 1 # wait for message to arrive, but don't test (-1)
    min_no_messages = -1
    max_no_messages = -1

    # Parameters for FrameControl FC
    BS=0
    ST=0
    FC_delay = 0 #no wait
    FC_flag = 48 #continue send
    FC_auto = False
    
    # send 11 requests now
    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xED\xA0\xF1\x26\xF1\x2E\xDA\x80\xF1\x8C\xDD\x00\xDD\x0B\xDD\x01\x49\x45\xDB\x72', "")
    can_mr_extra = ''
    
    SC.change_MF_FC(s, BS, ST, FC_delay, FC_flag, FC_auto)
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)


# teststep 9: test if DIDs are included in reply including those from combined DID
def step_9(stub, s, r, ns):
    global testresult
    #
    stepno = 9
    purpose = "test if all requested DIDs are included in reply"
    
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
    print ("Step9: messages received ", len(SC.can_messages[r]))
    print ("Step9: messages: ", SC.can_messages[r], "\n")
    print ("Step9: frames received ", len(SC.can_frames[r]))
    print ("Step9: frames: ", SC.can_frames[r], "\n")
    print ("Test if string contains all IDs expected:")

    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='EDA0')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F120')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F12A')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F12B')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F12E')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F18C')

    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F126')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F12E')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DA80')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F18C')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DD00')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DD0B')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DD01')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='4945')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DB72')


# teststep 10: verify extended session
def step_10(stub, s, r, ns):
    global testresult
    
    stepno = 10
    purpose = "Verify extended session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x03'
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    time.sleep(1)

# teststep 11: Change to default session
def step_11(stub, s, r, ns):
    global testresult
    
    stepno = 11
    purpose = "Change to default session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "DiagnosticSessionControl", b'\x01', "")
    can_mr_extra = ''
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)

    

def run():
    global testresult
    
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
    # action: send several requests at one time - requires SF to send
    # result: 
    step_2(network_stub, can_send, can_receive, can_namespace)
    
    # step3:
    # action: update received messages, verify if DID contained"
    # result: verify if DID contained
    step_3(network_stub, can_send, can_receive, can_namespace)
   
    # step4:
    # action: send 10 requests at one time
    # result: 
    step_4(network_stub, can_send, can_receive, can_namespace)

    # step5:
    # action: update received messages, verify if DID contained"
    # result: verify if DID contained
    step_5(network_stub, can_send, can_receive, can_namespace)

    # step6:
    # action: send 11 requests at one time
    # result: 
    step_6(network_stub, can_send, can_receive, can_namespace)

    # step7:
    # action: update received messages, verify if DID contained"
    # result: error message expected, as max DID request exceeded
    step_7(network_stub, can_send, can_receive, can_namespace)

    # step8:
    # action: send 10 requests at one time, containing combined DID
    # result: 
    step_8(network_stub, can_send, can_receive, can_namespace)

    # step9:
    # action: update received messages, verify if DID contained"
    # result: verify if DID contained - including those from combined DID
    step_9(network_stub, can_send, can_receive, can_namespace)

    # step10:
    # action: verify current session
    # result: BECM reports extended session
    step_10(network_stub, can_send, can_receive, can_namespace)

    # step 11:
    # action: # Change to Default session
    # result: BECM reports mode
    step_11(network_stub, can_send, can_receive, can_namespace)
    
    ############################################
    # postCondition
    ############################################
            
    print()
    print ("time ", time.time())
    print ("Testcase end: ", datetime.now())
    print ("Time needed for testrun (seconds): ", int(time.time() - starttime))

    print ("Do cleanup now...")
    print ("Stop all periodic signals sent")
    #SC.stop_heartbeat()
    SC.stop_periodic_all()
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