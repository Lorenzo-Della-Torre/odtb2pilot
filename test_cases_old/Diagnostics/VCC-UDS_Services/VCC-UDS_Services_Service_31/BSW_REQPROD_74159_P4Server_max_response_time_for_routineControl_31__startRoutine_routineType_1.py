# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-06-17
# version:  1.0
# reqprod:  74159

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

# teststep 1: get P2_max
def step_1(stub, s, r, ns):
    global testresult
    global P2_server_max
    
    stepno = 1
    purpose = "Get P2 server max value"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "DiagnosticSessionControl", b'\x01', "")
    can_mr_extra = ''
    
    SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    
    P2_server_max = int(SC.can_messages[r][0][2][8:10], 16)

    print(P2_server_max)

# teststep 2: verify RoutineControl start reply positively and Type1 is stopped
def step_2(stub, s, r, ns):
    global testresult
    global T1, T2
    stepno = 2
    purpose = "verify RoutineControl start reply positively and Type1 is stopped"
    timeout = 1 #wait a second for reply to be send
    min_no_messages = 1
    max_no_messages = 1
    
    can_m_send = SC.can_m_send( "RoutineControlRequestSID",b'\x02\x06', b'\x01')
    can_mr_extra = ''
   
    T1=time.time()
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    T2 = SC.can_messages[r][0][0]
    testresult = testresult and SuTe.PP_Decode_Routine_Control_response(SC.can_frames[r][0][2], "Type1,Completed")

def step_3():
    global testresult
    global T1, T2
    global P2_server_max
    stepno = 3
    purpose = "Verify (time receive message – time sending request) < P4_server_max"
    SuTe.print_test_purpose(stepno, purpose)
    jitter_testenv = 10
    if (P2_server_max + jitter_testenv) > (T2 - T1):
        testresult 
    else:
        testresult = False
    print ("T difference(s):", (P2_server_max + 10)/1000 - (T2 - T1))
    print ("Step ", stepno, " teststatus:", testresult, "\n")
    
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
    # action:Change to default session
    # result: positive reply with Parameters P2_server_max and P2*_server_max
    step_1(network_stub, can_send, can_receive, can_namespace)

    # step2:
    # action: send start RoutineControl signal in default mode
    # result: BECM sends positive reply
    step_2(network_stub, can_send, can_receive, can_namespace)

    # step 3:
    # action: Verify (time receive message – time sending request) < P4_server_max 
    # result: positive result
    step_3()

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
    print ()
    if testresult:
        print ("Testcase result: PASSED")
    else:
        print ("Testcase result: FAILED")

    
if __name__ == '__main__':
    run()
