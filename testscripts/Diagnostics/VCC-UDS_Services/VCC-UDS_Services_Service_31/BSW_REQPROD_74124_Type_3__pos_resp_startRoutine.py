# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-05-16
# version:  1.0
# reqprod:  74124

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
    SC.start_heartbeat(stub, "EcmFront1NMFr", "Front1CANCfg1", b'\x20\x40\x00\xFF\x00\x00\x00\x00', 0.8)
    
    
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

# teststep 1: send signal vehicle velocity < 3km/h  
def step_1(stub):  

    stepno = 1
    purpose = "send signal vehicle velocity < 3km/h"
    SuTe.print_test_purpose(stepno, purpose)
    #VCU1Front1Fr06, VehSpdLgtSafe
    SC.start_periodic(stub, 'VehSpdLgtSafe', True, "VCU1Front1Fr06", "Front1CANCfg1", b'\x80\xd5\x00\x00\x00\x00\x00\x00',0.015)

# teststep 2: Change to extended session
def step_2(stub, s, r, ns):
    global testresult
    
    stepno = 2
    purpose = "Change to Extended session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "DiagnosticSessionControl", b'\x03', "")
    can_mr_extra = ''
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)

# teststep 3: verify RoutineControlRequest is sent for Type 1
def step_3(stub, s, r, ns):
    global testresult
    
    stepno = 3
    purpose = "verify RoutineControl start(01) is sent in Extended Session"
    timeout = 1 #wait a second for reply to be send
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "RoutineControlRequestSID",b'\xDC\x00', b'\x01')
    can_mr_extra = ''
    
    print("can_m_send ",can_m_send)

    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    
    testresult = testresult and SuTe.PP_Decode_Routine_Control_response(SC.can_frames[r][0][2], "Type3,Currently active")

# teststep 4:  send signal vehicle velocity > 3 km/h   
def step_4(stub):

    stepno = 4
    purpose = "send signal vehicle velocity > 3km/h"
    SuTe.print_test_purpose(stepno, purpose)
    SC.set_periodic('VehSpdLgtSafe', True, "VCU1Front1Fr06", "Front1CANCfg1", b'\x80\xd6\x00\x00\x00\x00\x00\x00',0.015)
    time.sleep(2)

# teststep 5: verify Routine Type 3 is running
def step_5(stub, s, r, ns):
    global testresult
    
    stepno = 5
    purpose = "verify Routine 3 is running even with entry conditions not fulfilled"
    timeout = 1 #wait a second for reply to be send
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "RoutineControlRequestSID",b'\xDC\x00', b'\x01')
    can_mr_extra = ''

    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)

    # testresult = testresult and SuTe.PP_Decode_Routine_Control_response(SC.can_frames[r][0][2], "Type3,Aborted")  
    testresult = testresult and SuTe.PP_Decode_Routine_Control_response(SC.can_frames[r][0][2], "Type3,Currently active")
              
# teststep 6: verify Extended session
def step_6(stub, s, r, ns):
    global testresult
    
    stepno = 6
    purpose = "Verify Extended session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send =SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x03'
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
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
    # action: # send periodic signal vehicle velocity < 3km/h
    # result:
    step_1(network_stub)

    # step2:
    # action: change BECM to Extended session
    # result: BECM reply with mode
    step_2(network_stub, can_send, can_receive, can_namespace)

    # step3:
    # action: send start RoutineControl signal for Type 3 (01)
    # result: BECM sends positive reply
    step_3(network_stub, can_send, can_receive, can_namespace)

    # step 4:
    # action: # send periodic signal vehicle velocity > 3km/h
    # result:
    step_4(network_stub)

    # step5:
    # action: send start RoutineControl signal for Type 3 (01)
    # result: BECM sends positive reply
    step_5(network_stub, can_send, can_receive, can_namespace)
    
    # step6:
    # action: Verify Extended session active
    # result: BECM sends active mode
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
