# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-05-14
# version:  1.0
# reqprod:  76139 76140

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
    SC.start_periodic(stub, 'heartbeat', True, "EcmFront1NMFr", "Front1CANCfg1", b'\x20\x40\x00\xFF\x00\x00\x00\x00', 0.8)
    time.sleep(4) #wait for ECU startup   

    

    # timeout = more than maxtime script takes
    # needed as thread for registered signals won't stop without timeout
    #timeout = 300   #seconds
    timeout = 60   #seconds
    SC.subscribe_signal(stub, s, r, ns, timeout)
    #record signal we send as well
    SC.subscribe_signal(stub, r, s, ns, timeout)

    
    print()
    #step_0(stub, s, r, ns)
    
    print ("precondition testok:", testresult, "\n")

    
# teststep 0: Complete ECU Part/Serial Number(s)
def step_0(stub, s, r, ns):
    global testresult
    
    stepno = 0
    purpose = "Complete ECU Part/Serial Number(s)"
    timeout = 5
    min_no_messages = 1
    max_no_messages = 1
    
    can_m_send = SC.can_m_send( "ReadDataByIentifier", b'\xED\xA0', "")
    can_mr_extra = ''

    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    print(SuTe.PP_CombinedDID_EDA0(SC.can_messages[r][0][2], title=''))


# teststep 1: Change to programming session
def step_1(stub, s, r, ns):
    global testresult
    global T1, T2
    global P2_server_max
    
    stepno = 1
    purpose = "Change to Programming session"
    timeout = 1
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "DiagnosticSessionControl", b'\x02', "")
    can_mr_extra = ''
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    #time.sleep(1)

    T1 = time.time()
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    #time.sleep(1)
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='065002')
    P2_server_max = int(SC.can_messages[r][0][2][8:10], 16)
    T2 = SC.can_messages[r][0][0]
    time.sleep(1)

def step_2():
    global testresult
    global T1, T2
    global P2_server_max
    global jitter_testenv
    stepno = 2
    purpose = "Verify (time receive message – time sending request) less than P2_server_max"
    SuTe.print_test_purpose(stepno, purpose)
    if (P2_server_max + jitter_testenv) > (T2 - T1):
        testresult
    else:
        testresult = False
    print ("T difference(s):", (P2_server_max + 10)/1000 - (T2 - T1))
    print ("Step ", stepno, " teststatus:", testresult, "\n")


# teststep 3: Change to default session
def step_3(stub, s, r, ns):
    global testresult
    global T1, T2
    global P2_server_max
    stepno = 3
    purpose = "Change to default session"
    time.sleep(1)
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1
     
    can_m_send = SC.can_m_send( "DiagnosticSessionControl", b'\x01', "")
    can_mr_extra = ''
    T1 = time.time()
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    
    P2_server_max = int(SC.can_messages[r][0][2][8:10], 16)
    T2 = SC.can_messages[r][0][0]
    time.sleep(1)

def step_4():
    global testresult
    global T1, T2
    global P2_server_max
    global jitter_enstenv
    stepno = 4
    purpose = "Verify (time receive message – time sending request) less than P2_server_max"
    SuTe.print_test_purpose(stepno, purpose)
    if (P2_server_max + jitter_testenv) > (T2 - T1):
        testresult
    else:
        testresult = False
    print ("T difference(s):", (P2_server_max + 10)/1000 - (T2 - T1))
    print ("Step ", stepno, " teststatus:", testresult, "\n")

# teststep 5: Change to extended session
def step_5(stub, s, r, ns):
    global testresult
    global T1, T2
    global P2_server_max

    stepno = 5
    purpose = "Change to extended session"
    time.sleep(1)
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "DiagnosticSessionControl", b'\x03', "")
    can_mr_extra = ''
    T1 = time.time()
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)

    P2_server_max = int(SC.can_messages[r][0][2][8:10], 16)
    T2 = SC.can_messages[r][0][0]
    time.sleep(1)

def step_6():
    global testresult
    global T1, T2
    global P2_server_max
    global jitter_testenv
    stepno = 6
    purpose = "Verify (time receive message – time sending request) less than P2_server_max"
    SuTe.print_test_purpose(stepno, purpose)
    if (P2_server_max + jitter_testenv) > (T2 - T1):
        testresult
    else:
        testresult = False
    
    print ("T difference(s):", (P2_server_max + 10)/1000 - (T2 - T1))
    print ("Step ", stepno, " teststatus:", testresult, "\n")

# teststep 7: Change to default session
def step_7(stub, s, r, ns):
    global testresult
    global T1, T2
    global P2_server_max

    stepno = 7
    purpose = "Change to default session"
    time.sleep(1)
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "DiagnosticSessionControl", b'\x01', "")
    can_mr_extra = ''
    T1 = time.time()
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    
    P2_server_max = int(SC.can_messages[r][0][2][8:10], 16)
    T2 = SC.can_messages[r][0][0]
    time.sleep(1)

def step_8():
    global testresult
    global T1, T2
    global P2_server_max
    global jitter_testenv
    stepno = 8
    purpose = "Verify (time receive message – time sending request) less than P2_server_max"
    SuTe.print_test_purpose(stepno, purpose)
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
    can_namespace = SC.nspace_lookup("Front1CANCfg1")
    
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
    # action: Change to programming session
    # result: positive reply with Parameters P2_server_max and P2*_server_max
    step_1(network_stub, can_send, can_receive, can_namespace)

    # step 2:
    # action: Wait for the response message
    # result:(time receive message – time sending request) less than P2_server_max
    step_2()

    # step 3:
    # action: Change to default session
    # result: positive reply with Parameters P2_server_max and P2*_server_max
    step_3(network_stub, can_send, can_receive, can_namespace)

    # step 4:
    # action: Wait for the response message
    # result: (time receive message – time sending request) less than P2_server_max
    step_4()

    # step 5:
    # action: Change to extended session
    # result: positive reply with Parameters P2_server_max and P2*_server_max
    step_5(network_stub, can_send, can_receive, can_namespace)

    # step 6:
    # action: Wait for the response message
    # result: (time receive message – time sending request) less than P2_server_max
    step_6()

    # step 7:
    # action: Change to default session
    # result: positive reply with Parameters P2_server_max and P2*_server_max
    step_7(network_stub, can_send, can_receive, can_namespace)

    # step 8:
    # action: Wait for the response message
    # result: (time receive message – time sending request) less than P2_server_max
    step_8()

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
