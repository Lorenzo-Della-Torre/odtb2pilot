# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   hweiler (Hans-Klaus Weiler)
# date:     2019-05-17
# version:  1.0
# reqprod:  76171

#inspired by https://grpc.io/docs/tutorials/basic/python.html

# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   hweiler (Hans-Klaus Weiler)
# date:     2019-05-02
# version:  1.0
# reqprod:  76171

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
    SC.start_heartbeat(stub, "EcmFront1NMFr", "Front1CANCfg1", b'\x20\x40\x00\xFF\x00\x00\x00\x00', 0.8)        

    # timeout = more than maxtime script takes
    # needed as thread for registered signals won't stop without timeout
    #timeout = 300   #seconds
    timeout = 60   #seconds
    SC.subscribe_signal(stub, s, r, ns, timeout)
    #record signal we send as well
    SC.subscribe_signal(stub, r, s, ns, timeout)

    # Parameters for FrameControl FC VCU
    time.sleep(1)
    BS=0
    ST=0
    FC_delay = 0 #no wait
    FC_flag = 48 #continue send
    FC_auto = False
    SC.change_MF_FC(s, BS, ST, FC_delay, FC_flag, FC_auto)
    
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
    

# teststep 1: Change to programming session
def step_1(stub, s, r, ns):
    global testresult
    
    stepno = 1
    purpose = "Change to Extended session"
    timeout = 1
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "DiagnosticSessionControl", b'\x02', "")
    can_mr_extra = ''
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    #time.sleep(1)


# teststep 2: verify session
def step_2(stub, s, r, ns):
    global testresult
    
    stepno = 2
    purpose = "Verify programming session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x02'
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    time.sleep(1)

    
# teststep 3: send request DID - requires SF to send, MF for reply
def step_3(stub, s, r, ns):
    global testresult
    
    stepno = 3
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
    
    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x21', "")
    can_mr_extra = ''
    
    SC.change_MF_FC(s, BS, ST, FC_delay, FC_flag, FC_auto)
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)


# teststep 4: test if DIDs are included in reply
def step_4(stub, s, r, ns):
    global testresult
    
    stepno = 4
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
    print ("Step4: messages received ", len(SC.can_messages[r]))
    print ("Step4: messages: ", SC.can_messages[r], "\n")
    print ("Step4: frames received ", len(SC.can_frames[r]))
    print ("Step4: frames: ", SC.can_frames[r], "\n")
    print ("Test if string contains all IDs expected:")

    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F121')

    
# teststep 5: request another DID 
def step_5(stub, s, r, ns):
    global testresult
    
    stepno = 5
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
    
    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x2A', "")
    can_mr_extra = ''
    
    SC.change_MF_FC(s, BS, ST, FC_delay, FC_flag, FC_auto)
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)


# teststep 6: test if DIDs are included in reply
def step_6(stub, s, r, ns):
    global testresult
    
    stepno = 6
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
    print ("Step6: messages received ", len(SC.can_messages[r]))
    print ("Step6: messages: ", SC.can_messages[r], "\n")
    print ("Step6: frames received ", len(SC.can_frames[r]))
    print ("Step6: frames: ", SC.can_frames[r], "\n")
    print ("Test if string contains all IDs expected:")
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F12A')

    
# teststep 7: request 2 DID - same DID as requested single before
def step_7(stub, s, r, ns):
    global testresult
    
    stepno = 7
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
    
    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x21\xF1\x2A', "")
    can_mr_extra = ''
    
    SC.change_MF_FC(s, BS, ST, FC_delay, FC_flag, FC_auto)
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)


# teststep 8: Verify if number for requests limited in programming session
def step_8(stub, s, r, ns):
    global testresult
    #
    stepno = 8
    purpose = "Verify if number for requests limited in programming session"
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
    print ("Step8: messages received ", len(SC.can_messages[r]))
    print ("Step8: messages: ", SC.can_messages[r], "\n")
    print ("Step8: frames received ", len(SC.can_frames[r]))
    print ("Step8: frames: ", SC.can_frames[r], "\n")
    print ("Test if string contains all IDs expected:")

    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='037F223100000000')
    print ("Error  message: ")
    print ("SC.can_messages[r]",SC.can_messages[r][0][2]) 
    print (SuTe.PP_Decode_7F_response(SC.can_messages[r][0][2]))
    print ("Step ", stepno, " teststatus:", testresult, "\n")

    
# teststep 9: request combined DID EDA0
def step_9(stub, s, r, ns):
    global testresult
    
    stepno = 9
    purpose = "request combined DID EDA0"
    timeout = 1 # wait for message to arrive, but don't test (-1)
    min_no_messages = -1
    max_no_messages = -1

    # Parameters for FrameControl FC
    BS=0
    ST=0
    FC_delay = 0 #no wait
    FC_flag = 48 #continue send
    FC_auto = False
    
    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xED\xA0', "")
    can_mr_extra = ''
    
    SC.change_MF_FC(s, BS, ST, FC_delay, FC_flag, FC_auto)
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)


# teststep 10: verify if combined DID can be requested
def step_10(stub, s, r, ns):
    global testresult
    #
    stepno = 10
    purpose = "verify if combined DID can be requested"
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
    print ("Step8: messages received ", len(SC.can_messages[r]))
    print ("Step8: messages: ", SC.can_messages[r], "\n")
    print ("Step8: frames received ", len(SC.can_frames[r]))
    print ("Step8: frames: ", SC.can_frames[r], "\n")
    print ("Test if string contains all IDs expected:")

    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='EDA0')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F121')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F12A')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F12B')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F18C')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F125')



# teststep 11: verify session
def step_11(stub, s, r, ns):
    global testresult
    
    stepno = 11
    purpose = "Verify Programming session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x02'
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    time.sleep(1)

    # teststep 12: verify session
def step_12(stub, s, r, ns):
    global testresult
    
    stepno = 12
    purpose = "Change to Default session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "DiagnosticSessionControl", b'\x01', "")
    can_mr_extra = ''
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    time.sleep(1)

    # teststep 13: verify session
def step_13(stub, s, r, ns):
    global testresult
    
    stepno = 13
    purpose = "Verify default session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

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
    can_namespace = SC.nspace_lookup("Front1CANCfg1")

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
    # action: # Change to Programming session
    # result: BECM reports mode
    step_1(network_stub, can_send, can_receive, can_namespace)
    
    # step2:
    # action: verify current session
    # result: BECM reports programming session
    step_2(network_stub, can_send, can_receive, can_namespace)

    # step3:
    # action: send single requests
    # result: 
    step_3(network_stub, can_send, can_receive, can_namespace)
    
    # step4:
    # action: update received messages, verify if DID contained"
    # result: verify if DID contained
    step_4(network_stub, can_send, can_receive, can_namespace)
   
    # step5:
    # action: request another DID
    # result: 
    step_5(network_stub, can_send, can_receive, can_namespace)

    # step6:
    # action: update received messages, verify if DID contained"
    # result: verify if DID contained
    step_6(network_stub, can_send, can_receive, can_namespace)

    # step7:
    # action: request 2 DID
    # result: 
    step_7(network_stub, can_send, can_receive, can_namespace)

    # step8:
    # action: update received messages, verify if DID contained"
    # result: error message expected, as max DID request exceeded
    step_8(network_stub, can_send, can_receive, can_namespace)
    
    # step9:
    # action: send request containing combined DID
    # result: 
    step_9(network_stub, can_send, can_receive, can_namespace)

    # step10:
    # action: update received messages, verify if DID contained"
    # result: verify if DID contained from combined DID
    step_10(network_stub, can_send, can_receive, can_namespace)
        
    # step11:
    # action: verify current session
    # result: BECM reports programming session
    step_11(network_stub, can_send, can_receive, can_namespace)

    # step 12:
    # action: # Change to Default session
    # result: BECM reports mode
    step_12(network_stub, can_send, can_receive, can_namespace)

    # step13:
    # action: verify current session
    # result: BECM reports default session
    step_13(network_stub, can_send, can_receive, can_namespace)

    
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
    print ()
    if testresult:
        print ("Testcase result: PASSED")
    else:
        print ("Testcase result: FAILED")

    
if __name__ == '__main__':
    run()
