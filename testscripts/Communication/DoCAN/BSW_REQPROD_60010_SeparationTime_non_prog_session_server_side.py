# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   hweiler (Hans-Klaus Weiler)
# date:     2019-07-02
# version:  1.0
# reqprod:  60010

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

    
# teststep 2: send request requiring MF to send
def step_2(stub, s, r, ns):
    global testresult
    
    stepno = 2
    purpose = "send several requests at one time - requires MF in request"
    timeout = 1 # wait for message to arrive, but don't test (-1)
    min_no_messages = -1
    max_no_messages = -1
   
    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xDD\x02\xDD\x0A\xDD\x0C\x49\x47', "")
    can_mr_extra = ''
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
# verify FC parameters from BECM for BS
    print ("FC parameters used:")
    print ("Step ", stepno," frames received ", len(SC.can_frames[r]))
    print ("Step ", stepno," frames: ", SC.can_frames[r], "\n")
    print ("len FC ", len(SC.can_cf_received[r]))
    print ("FC: ", SC.can_cf_received[r])
    print ("Verify if FC is as required. Continue to send (0x30): 0x"+ int((SC.can_cf_received[r][0][2][0:2]),16).to_bytes(1, 'big').hex(), "ST: 0x"+ int((SC.can_cf_received[r][0][2][4:6]),16).to_bytes(1,'big').hex())
    print ("Verify ST less then 15ms: 15 > ", int((SC.can_cf_received[r][0][2][4:6]),16), ": ", (15 > int((SC.can_cf_received[r][0][2][4:6]),16) ))
    testresult = (15 > int((SC.can_cf_received[r][0][2][4:6]),16) ) and testresult
    #print ("FC: ", Support_CAN.can_cf_received)
    #testresult = SuTe.test_message(SC.can_cf_received[r], teststring='30000A0000000000') and testresult
    print ("Step ", stepno, " teststatus:", testresult, "\n")

# teststep 3: verify session
def step_3(stub, s, r, ns):
    global testresult
    
    stepno = 3
    purpose = "Verify default session"
    timeout = 1
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x03'
    
    testresult = SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages) and testresult


# teststep 4: Change to extended session
def step_4(stub, s, r, ns):
    global testresult
    
    stepno = 4
    purpose = "Change to extended session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "DiagnosticSessionControl", b'\x03', "")
    can_mr_extra = ''
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
 
# teststep 5: send request requiring MF to send
def step_5(stub, s, r, ns):
    global testresult
    
    stepno = 5
    purpose = "send several requests at one time - requires MF in request"
    timeout = 1 # wait for message to arrive, but don't test (-1)
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xDD\x02\xDD\x0A\xDD\x0C\x49\x47', "")
    can_mr_extra = ''
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
# verify FC parameters from BECM for BS
    print ("FC parameters used:")
    print ("Step ", stepno," frames received ", len(SC.can_frames[r]))
    print ("Step ", stepno," frames: ", SC.can_frames[r], "\n")
    print ("len FC ", len(SC.can_cf_received[r]))
    print ("FC: ", SC.can_cf_received[r])
    print ("Verify if FC is as required. Continue to send (0x30): 0x"+ int((SC.can_cf_received[r][0][2][0:2]),16).to_bytes(1, 'big').hex(), "ST: 0x"+ int((SC.can_cf_received[r][0][2][4:6]),16).to_bytes(1,'big').hex())
    print ("Verify ST less then 15ms: 15 > ", int((SC.can_cf_received[r][0][2][4:6]),16), ": ", (15 > int((SC.can_cf_received[r][0][2][4:6]),16) ))
    testresult = (15 > int((SC.can_cf_received[r][0][2][4:6]),16) ) and testresult
    print ("Step ", stepno, " teststatus:", testresult, "\n")


# teststep 6: verify session
def step_6(stub, s, r, ns):
    global testresult
    
    stepno = 6
    purpose = "Verify extended session"
    timeout = 5
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x03'
    
    testresult = SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages) and testresult
    time.sleep(1)


# teststep 7: Change to default session
def step_7(stub, s, r, ns):
    global testresult
    
    stepno = 7
    purpose = "Change to default session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "DiagnosticSessionControl", b'\x01', "")
    can_mr_extra = ''
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)



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
    
    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: verify current session
    # result: default session reported
    step_1(network_stub, can_send, can_receive, can_namespace)
    
    # step2:
    # action: send MF request
    # result: FC frame received with ST timing in required range
    step_2(network_stub, can_send, can_receive, can_namespace)

    # action: verify current session
    # result: default session reported
    step_3(network_stub, can_send, can_receive, can_namespace)

    # action: request extended session
    # result: change to extended session reported
    step_4(network_stub, can_send, can_receive, can_namespace)

    # action: send MF request
    # result: FC frame received with ST timing in required range
    step_5(network_stub, can_send, can_receive, can_namespace)

    # action: verify current session
    # result: extended session reported
    step_6(network_stub, can_send, can_receive, can_namespace)

    # action: request default session
    # result: change to default session reported
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